import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

/** Collecte les erreurs de la page (exceptions et console.error) pour vérifier qu'il n'y en a aucune. */
export const trackErrors = (page: Page) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  return errors;
};

/** Aucune violation d'accessibilité grave ou critique (règles WCAG 2.1 A et AA). */
export const expectAccessible = async (page: Page) => {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const serious = violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical",
  );
  expect(
    serious.map(
      (violation) =>
        `${violation.id} : ${violation.nodes.map((node) => node.target.join(" ")).join(", ")}`,
    ),
  ).toEqual([]);
};

/**
 * Prépare l'état du navigateur avant le chargement : session de démonstration (« rester connecté »)
 * et textes suivis, comme les écrirait l'application (@democracy-watch/state).
 */
export const signIn = async (page: Page, { followed = [] as string[] } = {}) => {
  await page.addInitScript((ids) => {
    if (window.sessionStorage.getItem("dw:e2e-init")) return;
    window.sessionStorage.setItem("dw:e2e-init", "1");
    const session = {
      email: "asso@example.org",
      remember: true,
      startedAt: "2026-10-20T10:00:00.000Z",
    };
    window.localStorage.setItem("dw:session", JSON.stringify({ state: { session }, version: 1 }));
    const texts = ids.map((id) => ({
      id,
      addedAt: "2026-10-20T10:00:00.000Z",
      articles: "tous",
      alerts: [],
      theme: null,
    }));
    window.localStorage.setItem("dw:suivi", JSON.stringify({ state: { texts }, version: 1 }));
  }, followed);
};
