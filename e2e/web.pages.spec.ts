import { expect, test } from "@playwright/test";
import { expectAccessible, signIn, trackErrors } from "./support.ts";

/** Chaque route (connecté, PJL 2436 suivi) : se charge sans erreur, affiche son titre, reste accessible. */
const PAGES = [
  { path: "/", title: "Votre veille" },
  { path: "/recherche?q=pesticides+écoles", title: "résultats pour « pesticides écoles »" },
  { path: "/textes", title: "Mes textes de loi (1)" },
  { path: "/textes/ajouter", title: "Ajouter des textes à l'étude" },
  { path: "/textes/pjl-2436", title: "Projet de loi d'orientation pour la transition agricole" },
  { path: "/textes/pjl-2436/articles/3", title: "Article 3 · Produits phytosanitaires" },
  { path: "/amendements", title: "Mes amendements suivis (13)" },
];

for (const { path, title } of PAGES) {
  test(`${path} se charge et reste accessible`, async ({ page }) => {
    const errors = trackErrors(page);
    await signIn(page, { followed: ["pjl-2436"] });
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(title);
    await expectAccessible(page);
    expect(errors).toEqual([]);
  });
}

test("/connexion se charge et reste accessible", async ({ page }) => {
  const errors = trackErrors(page);
  await page.goto("/connexion");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Gardez un œil sur vos amendements",
  );
  await expectAccessible(page);
  expect(errors).toEqual([]);
});

test("un texte inconnu affiche la page introuvable", async ({ page }) => {
  await signIn(page);
  await page.goto("/textes/inconnu");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Page introuvable");
});

test("la page déclare favicon, manifeste et image de partage", async ({ page }) => {
  await page.goto("/connexion");
  await expect(page.locator('link[rel="icon"][href="/favicon.svg"]')).toHaveCount(1);
  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute("href", "/site.webmanifest");
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
    "content",
    /og-image\.png/,
  );
});
