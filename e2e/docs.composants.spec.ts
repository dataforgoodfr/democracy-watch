import { readdirSync } from "node:fs";
import { expect, test } from "@playwright/test";
// Même calcul d'URL que la navigation générée (préfixes d'ordre retirés).
import { routeFromRelPath } from "../sites/docs/scripts/routes.mjs";
import { trackErrors } from "./support.ts";

const docs = new URL("../sites/docs/", import.meta.url);
const pages = readdirSync(new URL("03-front/03-composants/", docs), {
  recursive: true,
  encoding: "utf8",
})
  .filter((file) => file.endsWith(".mdx") && file !== "index.mdx")
  .map((file) => routeFromRelPath(`03-front/03-composants/${file}`));

test("il y a une page par composant", () => {
  expect(pages.length).toBeGreaterThanOrEqual(32);
});

for (const path of pages) {
  test(`composant ${path} : aperçus rendus, un bloc de code par aperçu`, async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 2, name: /Import/ })).toBeVisible();
    await expect(
      page.getByRole("heading", { level: 2, name: /Utilisation de base/ }),
    ).toBeVisible();

    const previews = page.locator(".dw-preview");
    const count = await previews.count();
    expect(count).toBeGreaterThan(0);
    for (let index = 0; index < count; index++) {
      const box = await previews.nth(index).boundingBox();
      expect(box?.height ?? 0, `aperçu ${index + 1} vide`).toBeGreaterThan(30);
    }
    // Import + un bloc de code par aperçu.
    await expect(page.locator("pre")).toHaveCount(count + 1);
    expect(errors).toEqual([]);
  });
}
