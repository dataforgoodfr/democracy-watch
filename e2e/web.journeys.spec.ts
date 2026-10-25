import { expect, test } from "@playwright/test";
import { signIn } from "./support.ts";

test("sans session : connexion puis retour à la page demandée", async ({ page }) => {
  await page.goto("/textes");
  await expect(page).toHaveURL(/\/connexion\?suite=%2Ftextes/);
  await page.getByLabel(/Adresse e-mail/).fill("asso@example.org");
  await page.getByLabel(/Mot de passe/).fill("secret");
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page).toHaveURL(/\/textes$/);
  await expect(page.getByText("asso@example.org")).toBeVisible();
});

test("cycle de suivi : sélectionner des textes, les suivre, ouvrir le kanban d'un article", async ({
  page,
}) => {
  await signIn(page);
  await page.goto("/textes/ajouter");
  await page.getByRole("checkbox", { name: /Sélectionner Projet de loi d'orientation/ }).check();
  await page
    .getByRole("checkbox", { name: /Sélectionner Proposition de loi visant à protéger/ })
    .check();
  await page.getByRole("button", { name: "Ajouter 2 textes à mon étude" }).click();

  await expect(page).toHaveURL(/\/textes$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mes textes de loi (2)");
  await page
    .getByRole("link", { name: "Projet de loi d'orientation pour la transition agricole" })
    .click();
  await page.getByRole("link", { name: "Art. 3 · Produits phytosanitaires" }).click();
  await expect(page.getByRole("region", { name: "Commission au fond — 6" })).toBeVisible();

  // Le suivi est conservé dans le navigateur.
  await page.reload();
  await expect(page.getByRole("link", { name: "Mes textes de loi (2)" })).toBeVisible();
});

test("rechercher depuis le header puis filtrer par étape", async ({ page }) => {
  await signIn(page);
  await page.goto("/");
  await page
    .getByRole("textbox", { name: /rechercher un texte de loi/i })
    .fill("pesticides écoles");
  await page.getByRole("button", { name: "Rechercher" }).click();
  await expect(page).toHaveURL(/\/recherche\?q=pesticides/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "résultats pour « pesticides écoles »",
  );

  // La case reflète l'URL : on clique, puis on attend la nouvelle URL.
  await page.getByRole("checkbox", { name: "Dépôt" }).click();
  await expect(page).toHaveURL(/etape=depot/);
  await expect(
    page.getByRole("link", { name: /Proposition de loi visant à protéger les enfants/ }),
  ).toBeVisible();
});

test("article : changer de vue", async ({ page }) => {
  await signIn(page, { followed: ["pjl-2436"] });
  await page.goto("/textes/pjl-2436/articles/3");
  await expect(page.getByRole("region", { name: "Commission au fond — 6" })).toBeVisible();
  await page.getByText("Liste", { exact: true }).click();
  await expect(page).toHaveURL(/vue=liste/);
  await expect(page.getByText("CE 31", { exact: true })).toBeVisible();
});

test("déconnexion", async ({ page }) => {
  await signIn(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Se déconnecter" }).click();
  await expect(page).toHaveURL(/\/connexion/);
});

test("navigation au clavier : lien d'évitement puis contenu", async ({ page }) => {
  await signIn(page);
  await page.goto("/textes");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Aller au contenu" })).toBeFocused();
});

test("mobile : la page reste utilisable sans défilement horizontal", async ({ page }) => {
  await signIn(page, { followed: ["pjl-2436"] });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/amendements");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});
