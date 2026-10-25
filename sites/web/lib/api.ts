import { createRepository, parseApiMode } from "@democracy-watch/api";

/**
 * Source des données, choisie au build :
 *   NEXT_PUBLIC_API_MODE=DEV_FRONT → données fictives (aucune API requise) ;
 *   NEXT_PUBLIC_API_MODE=API       → API FastAPI à NEXT_PUBLIC_API_URL.
 * Les accès `process.env.NEXT_PUBLIC_*` doivent rester littéraux pour être inlinés par Next.js.
 */
export const apiMode = parseApiMode(process.env.NEXT_PUBLIC_API_MODE);

export const createAppRepository = () =>
  createRepository({ mode: apiMode, baseUrl: process.env.NEXT_PUBLIC_API_URL });
