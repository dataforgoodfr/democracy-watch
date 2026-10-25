import { describe, expect, it } from "vitest";
import { hemicycleDots, PICTO_VIEWBOX, pictoSvg } from "./geometry.ts";

describe("pictogramme", () => {
  it("dessine quatre rangées de sièges dans le cadre", () => {
    const dots = hemicycleDots();
    expect(new Set(dots.map((dot) => dot.row))).toEqual(new Set([0, 1, 2, 3]));
    for (const dot of dots) {
      expect(dot.cx).toBeGreaterThanOrEqual(0);
      expect(dot.cx).toBeLessThanOrEqual(PICTO_VIEWBOX.width);
      expect(dot.cy).toBeGreaterThanOrEqual(0);
    }
  });

  it("est symétrique", () => {
    const dots = hemicycleDots();
    for (const dot of dots) {
      const mirror = dots.find(
        (other) => Math.abs(other.cx - (100 - dot.cx)) < 0.05 && Math.abs(other.cy - dot.cy) < 0.05,
      );
      expect(mirror, `${dot.cx},${dot.cy}`).toBeDefined();
    }
  });

  it("produit un SVG autonome", () => {
    expect(pictoSvg({ ink: "#17322E" })).toMatch(/^<svg xmlns="http:\/\/www.w3.org\/2000\/svg"/);
  });
});
