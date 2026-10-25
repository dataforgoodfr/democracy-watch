const dateFormat = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

/** « 2026-09-03 » → « 3 sept. 2026 ». */
export const formatDate = (iso: string) => dateFormat.format(new Date(`${iso}T12:00:00Z`));

/** Accord simple : 1 amendement, 2 amendements, 0 amendement. */
export const plural = (count: number, singular: string, pluralForm = `${singular}s`) =>
  `${count} ${count > 1 ? pluralForm : singular}`;

/** Jours restants avant une échéance (« J-1 »), à partir d'une date de référence. */
export const daysUntil = (iso: string, today: string) =>
  Math.round((Date.parse(`${iso}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86_400_000);
