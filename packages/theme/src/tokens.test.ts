// @vitest-environment node
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { contrastRatio } from "./contrast.ts";
import { cssVariables, tokensCss } from "./css.ts";
import { colors } from "./tokens.ts";

describe("tokens.css", () => {
  it("est à jour avec tokens.ts (sinon : pnpm --filter @democracy-watch/theme generate)", () => {
    const onDisk = readFileSync(new URL("./tokens.css", import.meta.url), "utf8");
    expect(onDisk).toBe(tokensCss());
  });

  it("ne déclare jamais deux fois la même variable", () => {
    const names = cssVariables().map(([name]) => name);
    expect(names.filter((name, index) => names.indexOf(name) !== index)).toEqual([]);
  });
});

// Ratios annoncés par le styleguide (arrondis au dixième, tolérance 0,1).
const blanc = colors["fond-surface"];
const vert = colors["texte-action"];
const annonces: [string, string, string, number][] = [
  ["vert encre sur blanc", vert, blanc, 13.7],
  ["vert encre sur jaune clair", vert, colors["fond-marque"], 12.6],
  ["sarcelle texte sur blanc", colors["texte-accent"], blanc, 6.0],
  ["gris 200 sur blanc", colors["texte-defaut"], blanc, 11.4],
  ["gris 425 sur blanc", colors["texte-mention"], blanc, 5.7],
  ["erreur sur blanc", colors["statut-erreur"], blanc, 5.8],
  ["succès sur blanc", colors["statut-succes"], blanc, 5.8],
  ["info sur blanc", colors["statut-info"], blanc, 5.8],
];

describe("contrastes du styleguide", () => {
  it.each(annonces)("%s ≈ %f:1", (_, fg, bg, expected) => {
    expect(Math.abs(contrastRatio(fg, bg) - expected)).toBeLessThan(0.15);
  });

  it("tous les textes de statut passent WCAG AA (4,5:1) sur leur fond", () => {
    for (const status of ["erreur", "succes", "avertissement", "info"] as const) {
      const fg = colors[`statut-${status}`];
      const bg = colors[`statut-${status}-fond`];
      expect(contrastRatio(fg, bg), status).toBeGreaterThanOrEqual(4.5);
    }
  });
});
