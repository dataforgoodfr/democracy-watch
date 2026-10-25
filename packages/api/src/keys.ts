import type { AmendmentFilters, SearchFilters, TextCatalogFilters } from "@democracy-watch/data";

/** Clés TanStack Query, centralisées pour pouvoir invalider précisément. */
export const queryKeys = {
  all: ["dw"] as const,
  search: (filters: SearchFilters) => [...queryKeys.all, "recherche", filters] as const,
  catalog: (filters: TextCatalogFilters) => [...queryKeys.all, "catalogue", filters] as const,
  texts: (ids: string[]) => [...queryKeys.all, "textes", ids] as const,
  text: (id: string) => [...queryKeys.all, "texte", id] as const,
  articles: (textId: string) => [...queryKeys.all, "texte", textId, "articles"] as const,
  article: (textId: string, number: string) =>
    [...queryKeys.all, "texte", textId, "article", number] as const,
  amendments: (filters: AmendmentFilters) => [...queryKeys.all, "amendements", filters] as const,
  commissions: () => [...queryKeys.all, "commissions"] as const,
};
