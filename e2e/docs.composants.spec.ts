import { readdirSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { trackErrors } from "./support.ts";

const dir = new URL("../sites/docs/02-design-system/composants/", import.meta.url);
const slugs = readdirSync(dir)
  .filter((file) => file.endsWith(".mdx") && file !== "index.mdx")
  .map((file) => file.replace(/\.mdx$/, ""));

test("il y a une page par composant", () => {
  expect(slugs.length).toBeGreaterThanOrEqual(30);
});

for (const slug of slugs) {
  test(`composant ${slug} : aperçus rendus, un bloc de code par aperçu`, async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto(`/02-design-system/composants/${slug}`);
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
