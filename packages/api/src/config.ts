import type { Repository } from "@democracy-watch/data";
import { createHttpRepository } from "./http.ts";
import { createMockRepository } from "./mock.ts";

/** DEV_FRONT : tout le front tourne sur les données fictives, sans API. API : appels HTTP. */
export type ApiMode = "DEV_FRONT" | "API";

export const parseApiMode = (value: string | undefined): ApiMode =>
  value === "DEV_FRONT" ? "DEV_FRONT" : "API";

export type RepositoryConfig = { mode: ApiMode; baseUrl?: string; latencyMs?: number };

/** Choisit l'implémentation selon le mode. En mode API, `baseUrl` est obligatoire. */
export const createRepository = ({ mode, baseUrl, latencyMs }: RepositoryConfig): Repository => {
  if (mode === "DEV_FRONT") return createMockRepository({ latencyMs });
  if (!baseUrl)
    throw new Error("NEXT_PUBLIC_API_URL est requis quand NEXT_PUBLIC_API_MODE vaut « API ».");
  return createHttpRepository({ baseUrl });
};
