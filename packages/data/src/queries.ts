/**
 * Requêtes pures sur un jeu de données en mémoire. Le dépôt (`repository.ts`) les expose
 * de façon asynchrone, comme le fera une API.
 */
import type {
  Amendment,
  AmendmentStatus,
  Article,
  Commission,
  ExaminationStage,
  GroupCode,
  LegislativeText,
  Page,
  TextStage,
  TextType,
} from "./types.ts";

export type Dataset = {
  texts: LegislativeText[];
  articles: Article[];
  amendments: Amendment[];
  commissions: Commission[];
};

// ─── Recherche plein texte ──────────────────────────────────────────────────

/** Minuscules, sans accents. */
export const normalize = (value: string) =>
  value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

/** Racine grossière : retire le pluriel (écoles → ecole). */
export const stem = (word: string) => normalize(word).replace(/(s|x)$/, "");

/** Synonymes inclus dans la recherche (« Synonymes inclus ✓ »). */
const SYNONYMS: Record<string, string[]> = {
  pesticide: ["phytosanitaire", "phytopharmaceutique"],
  ecole: ["creche", "etablissements accueillant des enfant"],
};

/** Termes de la requête, chacun avec ses variantes acceptées. */
export const queryTerms = (query: string) =>
  query
    .split(/\s+/)
    .map(stem)
    .filter((term) => term.length >= 2)
    .map((term) => [term, ...(SYNONYMS[term] ?? [])]);

/** Vrai si chaque terme (ou l'un de ses synonymes) apparaît dans l'un des champs. */
export const matches = (query: string, ...fields: (string | null | undefined)[]) => {
  const terms = queryTerms(query);
  if (terms.length === 0) return true;
  const haystack = normalize(fields.filter(Boolean).join(" "));
  return terms.every((variants) => variants.some((variant) => haystack.includes(variant)));
};

/** Racines à surligner dans les résultats (termes et synonymes). */
export const highlightStems = (query: string) => queryTerms(query).flat();

// ─── Filtres ────────────────────────────────────────────────────────────────

export type SearchTab = "tout" | "textes" | "articles" | "amendements";

export type SearchFilters = {
  q: string;
  tab: SearchTab;
  onlyFollowed: boolean;
  /** Textes suivis par l'utilisateur (état client), utilisés quand `onlyFollowed` est vrai. */
  followedIds: string[];
  stages: TextStage[];
  commissions: string[];
  groups: GroupCode[];
  since: string | null;
};

const textPassesFilters = (text: LegislativeText, filters: SearchFilters) =>
  (!filters.onlyFollowed || filters.followedIds.includes(text.id)) &&
  (filters.stages.length === 0 || filters.stages.includes(text.stage)) &&
  (filters.commissions.length === 0 ||
    filters.commissions.includes(text.leadCommissionId) ||
    text.opinionCommissionIds.some((id) => filters.commissions.includes(id)));

export type ArticleResult = Article & { text: LegislativeText; amendmentCount: number };
export type AmendmentResult = Amendment & { text: LegislativeText; article: Article | null };

export type SearchResults = {
  texts: LegislativeText[];
  articles: ArticleResult[];
  amendments: AmendmentResult[];
  counts: { tout: number; textes: number; articles: number; amendements: number };
  highlight: string[];
};

const byId = <T extends { id: string }>(items: T[]) =>
  new Map(items.map((item) => [item.id, item]));

export const search = (data: Dataset, filters: SearchFilters): SearchResults => {
  const textsById = byId(data.texts);
  const articlesById = byId(data.articles);
  const allowedTexts = data.texts.filter((text) => textPassesFilters(text, filters));
  const allowedIds = new Set(allowedTexts.map((text) => text.id));

  const texts = allowedTexts.filter((text) =>
    matches(filters.q, text.title, text.shortTitle, text.excerpt?.text),
  );

  const articles = data.articles
    .filter((article) => allowedIds.has(article.textId))
    .filter((article) => matches(filters.q, article.title, article.summary))
    .flatMap((article) => {
      const text = textsById.get(article.textId);
      if (!text) return [];
      const amendmentCount = data.amendments.filter((a) => a.articleId === article.id).length;
      return [{ ...article, text, amendmentCount }];
    });

  const amendments = data.amendments
    .filter((amendment) => allowedIds.has(amendment.textId))
    .filter(
      (amendment) => filters.groups.length === 0 || filters.groups.includes(amendment.author.group),
    )
    .filter((amendment) => !filters.since || amendment.depositedAt >= filters.since)
    .filter((amendment) => matches(filters.q, amendment.summary, amendment.number))
    .flatMap((amendment) => {
      const text = textsById.get(amendment.textId);
      if (!text) return [];
      return [{ ...amendment, text, article: articlesById.get(amendment.articleId) ?? null }];
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
};

// ─── Catalogue des textes (« Ajouter des textes à l'étude ») ───────────────

export type TextCatalogFilters = {
  q: string;
  types: TextType[];
  inProgressOnly: boolean;
  page: number;
  pageSize: number;
};

export const paginate = <T>(items: T[], page: number, pageSize: number): Page<T> => {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const current = Math.min(Math.max(1, page), pageCount);
  return {
    items: items.slice((current - 1) * pageSize, current * pageSize),
    total: items.length,
    page: current,
    pageCount,
  };
};

export const listTexts = (data: Dataset, filters: TextCatalogFilters): Page<LegislativeText> => {
  const items = data.texts
    .filter((text) => filters.types.length === 0 || filters.types.includes(text.type))
    .filter((text) => !filters.inProgressOnly || text.stage !== "adopte")
    .filter((text) => matches(filters.q, text.title, String(text.number), text.carriedBy));
  return paginate(items, filters.page, filters.pageSize);
};

// ─── Amendements des textes suivis ─────────────────────────────────────────

export type AmendmentFilters = {
  /** Périmètre : textes dont on liste les amendements (les textes suivis). */
  scope: string[];
  q: string;
  /** Filtre facultatif à l'intérieur du périmètre. */
  textIds: string[];
  groups: GroupCode[];
  statuses: AmendmentStatus[];
  stages: ExaminationStage[];
};

/** Amendements des textes du périmètre, filtrés. */
export const listAmendments = (data: Dataset, filters: AmendmentFilters): AmendmentResult[] => {
  const scope = byId(data.texts.filter((text) => filters.scope.includes(text.id)));
  const articlesById = byId(data.articles);
  return data.amendments
    .filter((amendment) => scope.has(amendment.textId))
    .filter(
      (amendment) => filters.textIds.length === 0 || filters.textIds.includes(amendment.textId),
    )
    .filter(
      (amendment) => filters.groups.length === 0 || filters.groups.includes(amendment.author.group),
    )
    .filter(
      (amendment) => filters.statuses.length === 0 || filters.statuses.includes(amendment.status),
    )
    .filter((amendment) => filters.stages.length === 0 || filters.stages.includes(amendment.stage))
    .filter((amendment) =>
      matches(filters.q, amendment.number, amendment.author.name, amendment.summary),
    )
    .flatMap((amendment) => {
      const text = scope.get(amendment.textId);
      if (!text) return [];
      return [{ ...amendment, text, article: articlesById.get(amendment.articleId) ?? null }];
    });
};

// ─── Article et ses amendements ─────────────────────────────────────────────

export type ArticleView = {
  text: LegislativeText;
  article: Article;
  amendments: Amendment[];
};

export const getArticleView = (
  data: Dataset,
  textId: string,
  articleNumber: string,
): ArticleView | null => {
  const text = data.texts.find((item) => item.id === textId);
  const article = data.articles.find(
    (item) => item.textId === textId && item.number === articleNumber,
  );
  if (!text || !article) return null;
  return {
    text,
    article,
    amendments: data.amendments.filter((item) => item.articleId === article.id),
  };
};

/** Amendements similaires à `amendment` (dans les deux sens du lien). */
export const similarAmendments = (amendment: Amendment, all: Amendment[]) =>
  all.filter(
    (other) =>
      other.id !== amendment.id &&
      (other.similarTo?.amendmentId === amendment.id ||
        amendment.similarTo?.amendmentId === other.id),
  );

/** Répartition des amendements par étape d'examen, dans l'ordre du parcours. */
export const EXAMINATION_STAGES: ExaminationStage[] = [
  "depose",
  "commission-fond",
  "commission-avis",
  "seance",
  "senat",
];

export const groupByStage = (amendments: Amendment[]) =>
  new Map(EXAMINATION_STAGES.map((stage) => [stage, amendments.filter((a) => a.stage === stage)]));
