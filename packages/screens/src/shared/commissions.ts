import type { Commission } from "@democracy-watch/data";

/** Nom d'une commission par identifiant (repli : l'identifiant). */
export const commissionNamer = (commissions: Commission[] | undefined) => (id: string) =>
  commissions?.find((commission) => commission.id === id)?.name ?? id;
