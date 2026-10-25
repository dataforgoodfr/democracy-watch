import { describe, expect, it } from "vitest";
import {
  type AmendmentFilters,
  getArticleView,
  groupByStage,
  listAmendments,
  listTexts,
  matches,
  paginate,
  type SearchFilters,
  search,
  similarAmendments,
} from "./queries.ts";
import { fixtureDataset as data } from "./repository.ts";

const searchFilters = (overrides: Partial<SearchFilters> = {}): SearchFilters => ({
  q: "",
  tab: "tout",
  onlyFollowed: false,
  followedIds: [],
  stages: [],
  commissions: [],
  groups: [],
  since: null,
  ...overrides,
});

describe("matches", () => {
  it("ignore la casse, les accents et le pluriel", () => {
    expect(matches("Écoles", "près des ecole")).toBe(true);
  });

  it("exige chaque terme", () => {
    expect(matches("pesticides écoles", "pesticides près des habitations")).toBe(false);
  });

  it("inclut les synonymes", () => {
    expect(matches("pesticides", "produits phytosanitaires")).toBe(true);
  });

  it("accepte une requête vide", () => {
    expect(matches("", "n'importe quoi")).toBe(true);
  });
});

describe("search", () => {
  it("retrouve les textes, articles et amendements de la maquette « pesticides écoles »", () => {
    const results = search(data, searchFilters({ q: "pesticides écoles" }));
    expect(results.texts.map((text) => text.number)).toEqual([2436, 2511]);
    expect(results.articles.map((article) => article.title)).toContain("Produits phytosanitaires");
    expect(results.amendments.map((amendment) => amendment.number)).toEqual(["CE 31", "CE 12"]);
    expect(results.counts.tout).toBe(
      results.counts.textes + results.counts.articles + results.counts.amendements,
    );
  });

  it("filtre par étape du texte", () => {
    const results = search(data, searchFilters({ q: "pesticides", stages: ["depot"] }));
    expect(results.texts.map((text) => text.id)).toEqual(["ppl-2511"]);
  });

  it("filtre les amendements par groupe", () => {
    const results = search(data, searchFilters({ groups: ["SOC"] }));
    expect(results.amendments.every((amendment) => amendment.author.group === "SOC")).toBe(true);
  });

  it("restreint aux textes suivis par l'utilisateur", () => {
    const results = search(data, searchFilters({ onlyFollowed: true, followedIds: ["ppl-2511"] }));
    expect(results.texts.map((text) => text.id)).toEqual(["ppl-2511"]);
    expect(results.amendments).toEqual([]);
  });
});

describe("listTexts", () => {
  it("filtre par type et pagine", () => {
    const page = listTexts(data, {
      q: "",
      types: ["PPL"],
      inProgressOnly: false,
      page: 1,
      pageSize: 2,
    });
    expect(page.items).toHaveLength(2);
    expect(page.total).toBe(3);
    expect(page.pageCount).toBe(2);
  });

  it("cherche par numéro", () => {
    const page = listTexts(data, {
      q: "2390",
      types: [],
      inProgressOnly: false,
      page: 1,
      pageSize: 5,
    });
    expect(page.items.map((text) => text.id)).toEqual(["ppl-2390"]);
  });
});

describe("paginate", () => {
  it("borne la page demandée", () => {
    expect(paginate([1, 2, 3], 9, 2)).toEqual({ items: [3], total: 3, page: 2, pageCount: 2 });
  });
});

describe("amendements", () => {
  const none: AmendmentFilters = {
    scope: ["pjl-2436"],
    q: "",
    textIds: [],
    groups: [],
    statuses: [],
    stages: [],
  };

  it("ne liste que les amendements des textes du périmètre", () => {
    const results = listAmendments(data, none);
    expect(results.every((amendment) => amendment.textId === "pjl-2436")).toBe(true);
    expect(results).toHaveLength(13);
    expect(listAmendments(data, { ...none, scope: [] })).toEqual([]);
  });

  it("filtre par statut et par auteur", () => {
    const results = listAmendments(data, { ...none, q: "Garnier", statuses: ["adopte"] });
    expect(results.map((amendment) => amendment.number)).toEqual(["CE 31"]);
  });

  it("regroupe l'article 3 par étape comme la maquette « avancement »", () => {
    const view = getArticleView(data, "pjl-2436", "3");
    expect(view?.amendments).toHaveLength(8);
    const stages = groupByStage(view?.amendments ?? []);
    expect(stages.get("commission-fond")).toHaveLength(6);
    expect(stages.get("commission-avis")).toHaveLength(2);
    expect(stages.get("depose")).toHaveLength(0);
  });

  it("trouve les similaires dans les deux sens", () => {
    const ce23 = data.amendments.find((amendment) => amendment.id === "ce-23");
    if (!ce23) throw new Error("CE 23 absent des données fictives");
    const similar = similarAmendments(ce23, data.amendments);
    expect(similar.map((amendment) => amendment.number).sort()).toEqual(["CD 14", "CE 61"]);
  });

  it("renvoie null pour un article inconnu", () => {
    expect(getArticleView(data, "pjl-2436", "99")).toBeNull();
  });
});
