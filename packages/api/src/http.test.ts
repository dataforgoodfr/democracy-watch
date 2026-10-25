import { describe, expect, it } from "vitest";
import { createRepository, parseApiMode } from "./config.ts";
import { ApiError, createHttpRepository } from "./http.ts";

const DOSSIER = {
  uid: "DLR5L17N2436",
  legislature: 17,
  titre: "Projet de loi d'orientation pour la transition agricole",
  titre_court: "PJL transition agricole",
  procedure_libelle: "Projet de loi ordinaire",
  etat: "en_cours",
  date_depot: "2026-09-03T00:00:00",
  commissions: [
    { uid: "PO1", slug: "affaires-economiques", nom: "Affaires économiques", role: "fond" },
    { uid: "PO2", slug: "developpement-durable", nom: "Développement durable", role: "avis" },
  ],
  textes: [{ texte_ref: "PRJLANR5L17B2436", articles: 6 }],
};

const ARTICLES = [
  {
    texte_ref: "PRJLANR5L17B2436",
    numero: "3",
    libelle: "Produits phytosanitaires",
    ordre: 3,
    contenu: "I. – L'utilisation…",
  },
];

const amendement = (numero: string, sort: string | null) => ({
  uid: `AM-${numero}`,
  numero,
  legislature: 17,
  chambre: "assemblee",
  auteur_libelle: "M. Garnier",
  groupe_ref: "RN",
  texte_ref: "PRJLANR5L17B2436",
  article_vise: "Article 3",
  dispositif: "<p>Remplacer « peut » par « doit ».</p>",
  sort,
  cosignataires: 3,
});

const AMENDEMENTS = [
  amendement("CE31", "Adopté"),
  amendement("CE12", "Rejeté"),
  amendement("CD14", null),
];

const fakeFetch = (calls: string[]) =>
  (async (url: string) => {
    calls.push(url);
    const path = new URL(url).pathname;
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
    if (path === "/api/dossiers/DLR5L17N2436") return json(DOSSIER);
    if (path.startsWith("/api/dossiers/")) return json({ detail: "Dossier introuvable" }, 404);
    if (path.endsWith("/articles")) return json(ARTICLES);
    if (path.endsWith("/amendements")) return json(AMENDEMENTS);
    if (path === "/api/search")
      return json({
        mode: "grouped",
        page: 1,
        results: { dossiers: { hits: [DOSSIER], total: 1 } },
      });
    return json({ detail: "erreur" }, 500);
  }) as typeof fetch;

describe("dépôt HTTP", () => {
  const calls: string[] = [];
  const repository = createHttpRepository({ baseUrl: "https://api.test", fetch: fakeFetch(calls) });

  it("convertit une fiche de dossier en texte", async () => {
    const text = await repository.getText("DLR5L17N2436");
    expect(text).toMatchObject({
      id: "DLR5L17N2436",
      type: "PJL",
      number: 2436,
      leadCommissionId: "affaires-economiques",
    });
  });

  it("renvoie null pour un dossier inconnu", async () => {
    expect(await repository.getText("INCONNU")).toBeNull();
  });

  it("construit la vue « avancement » d'un article depuis les endpoints", async () => {
    const view = await repository.getArticleView("DLR5L17N2436", "3");
    expect(view?.article.title).toBe("Produits phytosanitaires");
    expect(view?.amendments.map((a) => [a.number, a.stage, a.status])).toEqual([
      ["CE 31", "commission-fond", "adopte"],
      ["CE 12", "commission-fond", "rejete"],
      ["CD 14", "commission-avis", "en-attente"],
    ]);
    expect(view?.amendments[0]?.summary).toBe("Remplacer « peut » par « doit ».");
  });

  it("filtre les amendements des textes suivis avec les mêmes règles que le mode mock", async () => {
    const results = await repository.listAmendments({
      scope: ["DLR5L17N2436"],
      q: "",
      textIds: [],
      groups: [],
      statuses: ["adopte"],
      stages: [],
    });
    expect(results.map((amendment) => amendment.number)).toEqual(["CE 31"]);
  });

  it("passe les paramètres de la RFC à /api/search", async () => {
    await repository.listTexts({
      q: "agricole",
      types: [],
      inProgressOnly: true,
      page: 2,
      pageSize: 5,
    });
    const url = new URL(calls.at(-1) ?? "");
    expect(url.pathname).toBe("/api/search");
    expect(url.searchParams.getAll("types")).toEqual(["dossiers"]);
    expect(url.searchParams.get("legislature")).toBe("17");
    expect(url.searchParams.get("page")).toBe("2");
  });

  it("signale une erreur serveur", async () => {
    const failing = createHttpRepository({
      baseUrl: "https://api.test",
      fetch: (async () => new Response("", { status: 503 })) as typeof fetch,
    });
    await expect(failing.getText("DLR5L17N2436")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("mode", () => {
  it("DEV_FRONT active les données fictives, sinon l'API", async () => {
    expect(parseApiMode("DEV_FRONT")).toBe("DEV_FRONT");
    expect(parseApiMode(undefined)).toBe("API");
    const mock = createRepository({ mode: "DEV_FRONT", latencyMs: 0 });
    expect((await mock.getText("pjl-2436"))?.shortTitle).toBe("PJL transition agricole");
    expect(() => createRepository({ mode: "API" })).toThrow(/NEXT_PUBLIC_API_URL/);
  });
});
