import { expect, test } from "@playwright/test";
import { trackErrors } from "./support.ts";

const PAGES = [
  { path: "/", title: "Democracy Watch" },
  { path: "/00-produit/notions-metier", title: "Notions métier à connaître" },
  { path: "/01-demarrer", title: "Installation" },
  { path: "/02-design-system", title: "Principes et règles" },
  { path: "/02-design-system/couleurs", title: "Couleurs" },
  { path: "/02-design-system/logo", title: "Logo et favicons" },
  { path: "/03-architecture", title: "Architecture" },
  { path: "/03-architecture/pages", title: "Pages et écrans" },
  { path: "/03-architecture/donnees", title: "Données, navigation, connexion" },
  { path: "/04-serveur/api", title: "API" },
  { path: "/05-roadmap", title: "Roadmap" },
];

for (const { path, title } of PAGES) {
  test(`doc ${path}`, async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(title);
    expect(errors).toEqual([]);
  });
}

test("les schémas Mermaid sont rendus", async ({ page }) => {
  await page.goto("/03-architecture/donnees");
  await expect(page.locator(".dw-mermaid svg").first()).toBeVisible();
});

test("les nuanciers sont lus depuis les tokens", async ({ page }) => {
  await page.goto("/02-design-system/couleurs");
  await expect(page.getByText("--dw-fond-action")).toBeVisible();
  await expect(page.getByText("#17322E").first()).toBeVisible();
});
