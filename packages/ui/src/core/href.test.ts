import { describe, expect, it } from "vitest";
import { asArray, buildHref, toggle } from "./href.ts";

describe("buildHref", () => {
  it("omet les valeurs vides et répète les listes", () => {
    expect(
      buildHref("/recherche", {
        q: "pesticides",
        stage: ["commission", "seance"],
        vide: "",
        non: false,
      }),
    ).toBe("/recherche?q=pesticides&stage=commission&stage=seance");
  });

  it("renvoie le chemin seul sans paramètre", () => {
    expect(buildHref("/textes", { page: null })).toBe("/textes");
  });
});

describe("toggle / asArray", () => {
  it("ajoute puis retire une valeur", () => {
    expect(toggle(["a"], "b")).toEqual(["a", "b"]);
    expect(toggle(["a", "b"], "a")).toEqual(["b"]);
  });

  it("normalise un paramètre d'URL", () => {
    expect(asArray(undefined)).toEqual([]);
    expect(asArray("x")).toEqual(["x"]);
  });
});
