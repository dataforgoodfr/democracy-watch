import { buildHref } from "@democracy-watch/ui";
import { describe, expect, it } from "vitest";
import { parseAddTextsParams } from "./add-texts/params.ts";
import { parseArticleParams } from "./article/params.ts";
import { parseSearchParams, searchParamsOf } from "./search/params.ts";

describe("paramètres d'URL", () => {
  it("recherche : lecture tolérante et aller-retour", () => {
    const filters = parseSearchParams({
      q: " pesticides ",
      etape: ["commission", "seance"],
      groupe: "SOC",
      type: "inconnu",
    });
    expect(filters).toMatchObject({
      q: "pesticides",
      tab: "tout",
      stages: ["commission", "seance"],
      groups: ["SOC"],
      followedIds: [],
    });
    expect(buildHref("/recherche", searchParamsOf(filters))).toBe(
      "/recherche?q=pesticides&etape=commission&etape=seance&groupe=SOC",
    );
  });

  it("ajout de textes : en cours d'examen par défaut, page bornée", () => {
    expect(parseAddTextsParams({ page: "-3" })).toEqual({
      q: "",
      types: [],
      inProgressOnly: true,
      page: 1,
    });
    expect(parseAddTextsParams({ encours: "0", type: "PPL" }).inProgressOnly).toBe(false);
  });

  it("article : vue « avancement » par défaut", () => {
    expect(parseArticleParams({}).view).toBe("avancement");
    expect(parseArticleParams({ vue: "groupe", similaires: "1" })).toEqual({
      q: "",
      view: "groupe",
      groupSimilar: true,
    });
  });
});
