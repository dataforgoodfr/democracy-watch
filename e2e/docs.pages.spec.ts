import { expect, test } from "@playwright/test";
import { trackErrors } from "./support.ts";

const PAGES = [
  { path: "/", title: "Democracy Watch" },
  { path: "/produit/notions-metier", title: "Notions métier à connaître" },
  { path: "/produit/cycle-de-vie", title: "Cycle de vie d'un amendement" },
  { path: "/accueil/demarrer", title: "Installation" },
  { path: "/front/design-system", title: "Principes et règles" },
  { path: "/front/design-system/couleurs", title: "Couleurs" },
  { path: "/front/design-system/logo", title: "Logo et favicons" },
  { path: "/front/architecture", title: "Architecture" },
  { path: "/front/architecture/pages", title: "Pages et écrans" },
  { path: "/front/architecture/donnees", title: "Données, navigation, connexion" },
  { path: "/serveur/api", title: "API" },
  { path: "/data", title: "Données" },
  { path: "/roadmap", title: "Roadmap" },
  { path: "/roadmap/suivi-de-projet", title: "Suivi de projet" },
  { path: "/roadmap/analytics", title: "Analytics (Rybbit)" },
  { path: "/roadmap/observability", title: "Observabilité (OpenObserve)" },
  { path: "/roadmap/produit-front", title: "Kanban — Produit et front" },
  { path: "/roadmap/donnees-api-ops", title: "Kanban — Données, API et ops" },
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
  await page.goto("/front/architecture/donnees");
  await expect(page.locator(".dw-mermaid svg").first()).toBeVisible();
});

test("les nuanciers sont lus depuis les tokens", async ({ page }) => {
  await page.goto("/front/design-system/couleurs");
  await expect(page.getByText("--dw-fond-action")).toBeVisible();
  await expect(page.getByText("#17322E").first()).toBeVisible();
});

test("les deux Kanban ont les sept colonnes", async ({ page }) => {
  for (const path of ["/roadmap/produit-front", "/roadmap/donnees-api-ops"]) {
    await page.goto(path);
    for (const column of [
      "Backlog",
      "Not Started",
      "To Implement",
      "In Progress",
      "In Testing",
      "In Review",
      "Done",
    ]) {
      await expect(
        page.getByRole("region", { name: new RegExp(`^${column} — \\d+$`) }),
      ).toBeVisible();
    }
  }
});
