import { expect, test } from "@playwright/test";
import tickets from "../sites/docs/src/roadmap/issues.generated.json" with { type: "json" };
import { trackErrors } from "./support.ts";

// Index généré depuis les fiches par scripts/generate-roadmap.mjs, qui valide déjà statuts et
// dépendances ; `pnpm check` garantit qu'il est à jour.
const STATUSES = [
  "Backlog",
  "Not Started",
  "To Implement",
  "In Progress",
  "In Testing",
  "In Review",
  "Done",
];

test("les fiches de tickets sont cohérentes", () => {
  const ids = tickets.map((ticket) => ticket.id);
  expect(new Set(ids).size).toBe(ids.length);
  for (let n = 1; n <= 43; n++) expect(ids).toContain(`DW-${String(n).padStart(2, "0")}`);
  for (const ticket of tickets) {
    expect(STATUSES, ticket.id).toContain(ticket.status);
    for (const dependency of ticket.dependsOn ?? [])
      expect(ids, `${ticket.id} → ${dependency}`).toContain(dependency);
  }
});

for (const ticket of tickets) {
  test(`fiche ${ticket.id}`, async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto(ticket.path);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(ticket.id);
    await expect(page.getByRole("heading", { level: 2, name: /Liens/ })).toBeVisible();
    await expect(
      page.getByRole("link", { name: /^Kanban (Produit et front|Données, API et ops)$/ }),
    ).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("une carte du Kanban ouvre la fiche du ticket", async ({ page }) => {
  await page.goto("/roadmap/produit-front");
  await page
    .getByRole("region", { name: /^Not Started — \d+$/ })
    .getByRole("link", { name: "DW-18" })
    .click();
  await expect(page).toHaveURL(/\/roadmap\/issues\/e3-kanban-des-amendements\/dw-18$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("DW-18");
});
