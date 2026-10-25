/**
 * Dépôt de données branché sur l'API FastAPI (voir la RFC « API » et server/democracy_watch/api).
 * Les réponses sont converties vers le modèle du front, puis les mêmes requêtes pures que le mode
 * mock (`@democracy-watch/data`) s'appliquent : filtres et regroupements se comportent pareil.
 */
import {
  type AmendmentResult,
  type ArticleResult,
  type Dataset,
  getArticleView,
  highlightStems,
  type LegislativeText,
  listAmendments,
  type Repository,
  type SearchTab,
} from "@democracy-watch/data";
import type { AmendementDto, ArticleDto, DossierDto, SearchResponseDto } from "./dto.ts";
import { leadPrefixOf, toAmendment, toArticle, toCommission, toText } from "./mapping.ts";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly path: string,
  ) {
    super(`L'API a répondu ${status} pour ${path}`);
    this.name = "ApiError";
  }
}

type Params = Record<string, string | number | (string | number)[] | null | undefined>;

/** Document renvoyé par la recherche (Meilisearch) : champs non garantis. */
type Hit = Record<string, unknown>;

const text = (value: unknown) => (typeof value === "string" ? value : null);

export type HttpRepositoryOptions = {
  /** URL de l'API, sans « / » final (ex. https://api.democracy-watch.fr). */
  baseUrl: string;
  fetch?: typeof fetch;
  legislature?: number;
};

const TYPES_BY_TAB: Record<SearchTab, string[]> = {
  tout: ["dossiers", "articles", "amendements"],
  textes: ["dossiers"],
  articles: ["articles"],
  amendements: ["amendements"],
};

export const createHttpRepository = ({
  baseUrl,
  fetch: fetcher = globalThis.fetch,
  legislature = 17,
}: HttpRepositoryOptions): Repository => {
  const get = async <T>(path: string, params: Params = {}): Promise<T | null> => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      for (const item of Array.isArray(value) ? value : [value]) {
        if (item !== null && item !== undefined && item !== "") query.append(key, String(item));
      }
    }
    const url = `${baseUrl}${path}${query.size ? `?${query}` : ""}`;
    const response = await fetcher(url, { headers: { Accept: "application/json" } });
    if (response.status === 404) return null;
    if (!response.ok) throw new ApiError(response.status, path);
    // Frontière réseau : le contrat est celui des schémas FastAPI (dto.ts).
    return (await response.json()) as T;
  };

  const getDossier = (uid: string) => get<DossierDto>(`/api/dossiers/${encodeURIComponent(uid)}`);

  /** Un texte avec ses articles et ses amendements, sous forme de jeu de données. */
  const textDataset = async (textId: string): Promise<Dataset | null> => {
    const dossier = await getDossier(textId);
    if (!dossier) return null;
    const texteRef = dossier.textes[0]?.texte_ref;
    const [articles, amendements] = texteRef
      ? await Promise.all([
          get<ArticleDto[]>(`/api/textes/${encodeURIComponent(texteRef)}/articles`),
          get<AmendementDto[]>(`/api/textes/${encodeURIComponent(texteRef)}/amendements`),
        ])
      : [[], []];
    const leadPrefix = leadPrefixOf(amendements ?? []);
    const text = { ...toText(dossier), amendmentCount: amendements?.length ?? 0 };
    return {
      texts: [text],
      articles: (articles ?? []).map((article) => toArticle(article, textId)),
      amendments: (amendements ?? []).map((amendement) =>
        toAmendment(amendement, textId, leadPrefix),
      ),
      commissions: dossier.commissions.map(toCommission),
    };
  };

  const merge = (datasets: (Dataset | null)[]): Dataset => {
    const present = datasets.filter((dataset): dataset is Dataset => dataset !== null);
    return {
      texts: present.flatMap((dataset) => dataset.texts),
      articles: present.flatMap((dataset) => dataset.articles),
      amendments: present.flatMap((dataset) => dataset.amendments),
      commissions: present.flatMap((dataset) => dataset.commissions),
    };
  };

  /** Document Meilisearch d'un dossier → texte (champs absents : valeurs neutres). */
  const hitToText = (hit: Hit) =>
    toText({
      uid: text(hit.uid) ?? "",
      legislature,
      titre: text(hit.titre) ?? "",
      titre_court: text(hit.titre_court),
      procedure_libelle: text(hit.procedure_libelle),
      etat: text(hit.etat),
      date_depot: text(hit.date_depot),
      commissions: [],
      textes: [],
    });

  /** Texte minimal pour rattacher un article ou un amendement trouvé par la recherche. */
  const parentText = (hit: Hit): LegislativeText =>
    hitToText({
      uid: hit.dossier_uid ?? hit.texte_ref,
      titre: hit.dossier_titre ?? hit.texte_ref,
      titre_court: hit.dossier_titre_court ?? hit.dossier_titre ?? hit.texte_ref,
    });

  const hitToArticle = (hit: Hit): ArticleDto => ({
    texte_ref: text(hit.texte_ref) ?? "",
    numero: text(hit.numero) ?? "",
    libelle: text(hit.libelle) ?? "",
    ordre: typeof hit.ordre === "number" ? hit.ordre : 0,
    contenu: text(hit.contenu) ?? "",
  });

  const hitToAmendement = (hit: Hit): AmendementDto => ({
    uid: text(hit.uid) ?? "",
    numero: text(hit.numero) ?? "",
    legislature,
    chambre: text(hit.chambre) ?? "assemblee",
    auteur_libelle: text(hit.auteur_libelle),
    groupe_ref: text(hit.groupe_ref) ?? text(hit.groupe_politique),
    texte_ref: text(hit.texte_ref),
    article_vise: text(hit.article_vise),
    dispositif: text(hit.dispositif),
    expose_sommaire: text(hit.expose_sommaire),
    sort: text(hit.sort),
    date_depot: text(hit.date_depot),
    cosignataires: typeof hit.cosignataires === "number" ? hit.cosignataires : 0,
  });

  return {
    search: async (filters) => {
      const response = await get<SearchResponseDto>("/api/search", {
        q: filters.q,
        types: TYPES_BY_TAB[filters.tab],
        mode: "grouped",
        legislature,
        groupe_politique: filters.groups,
        date_min: filters.since,
        limit: 50,
      });
      const results = response?.results ?? {};
      const followed = (text: LegislativeText) =>
        !filters.onlyFollowed || filters.followedIds.includes(text.id);
      const texts = (results.dossiers?.hits ?? []).map(hitToText).filter(followed);
      const articles: ArticleResult[] = (results.articles?.hits ?? []).flatMap((hit) => {
        const text = parentText(hit);
        if (!followed(text)) return [];
        return [{ ...toArticle(hitToArticle(hit), text.id), text, amendmentCount: 0 }];
      });
      const amendments: AmendmentResult[] = (results.amendements?.hits ?? []).flatMap((hit) => {
        const text = parentText(hit);
        if (!followed(text)) return [];
        return [{ ...toAmendment(hitToAmendement(hit), text.id, null), text, article: null }];
      });
      return {
        texts,
        articles,
        amendments,
        counts: {
          tout: texts.length + articles.length + amendments.length,
          textes: texts.length,
          articles: articles.length,
          amendements: amendments.length,
        },
        highlight: highlightStems(filters.q),
      };
    },

    listTexts: async (filters) => {
      const pageSize = filters.pageSize;
      const response = await get<SearchResponseDto>("/api/search", {
        q: filters.q,
        types: ["dossiers"],
        legislature,
        page: filters.page,
        limit: pageSize,
      });
      const dossiers = response?.results?.dossiers;
      const items = (dossiers?.hits ?? [])
        .map(hitToText)
        .filter((text) => filters.types.length === 0 || filters.types.includes(text.type))
        .filter((text) => !filters.inProgressOnly || text.stage !== "adopte");
      const total = dossiers?.total ?? items.length;
      return {
        items,
        total,
        page: filters.page,
        pageCount: Math.max(1, Math.ceil(total / pageSize)),
      };
    },

    getTexts: async (ids) => {
      const dossiers = await Promise.all(ids.map(getDossier));
      return dossiers.flatMap((dossier) => (dossier ? [toText(dossier)] : []));
    },

    getText: async (id) => {
      const dossier = await getDossier(id);
      return dossier ? toText(dossier) : null;
    },

    listArticles: async (textId) => {
      const data = await textDataset(textId);
      if (!data) return [];
      return data.articles.map((article) => ({
        ...article,
        amendmentCount: data.amendments.filter((amendment) => amendment.articleId === article.id)
          .length,
      }));
    },

    getArticleView: async (textId, articleNumber) => {
      const data = await textDataset(textId);
      return data ? getArticleView(data, textId, articleNumber) : null;
    },

    listAmendments: async (filters) =>
      listAmendments(merge(await Promise.all(filters.scope.map(textDataset))), filters),

    // Pas encore d'endpoint : les noms de commission viennent des fiches de dossier.
    listCommissions: async () => [],

    referenceDate: () => new Date().toISOString().slice(0, 10),
  };
};
