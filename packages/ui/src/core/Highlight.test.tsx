import { describe, expect, it } from "vitest";
import { highlightSegments } from "./Highlight.tsx";

describe("highlightSegments", () => {
  it("marque les mots qui commencent par une racine, sans tenir compte des accents", () => {
    const marked = highlightSegments("Interdit les pesticides près des écoles.", [
      "pesticide",
      "ecole",
    ])
      .filter((segment) => segment.match)
      .map((segment) => segment.text);
    expect(marked).toEqual(["pesticides", "écoles"]);
  });

  it("accepte des racines accentuées ou en majuscules", () => {
    const marked = highlightSegments("près des écoles", ["Écoles"]).filter(
      (segment) => segment.match,
    );
    expect(marked.map((segment) => segment.text)).toEqual(["écoles"]);
  });

  it("ne marque rien sans recherche", () => {
    expect(highlightSegments("texte", []).some((segment) => segment.match)).toBe(false);
  });
});
