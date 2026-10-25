"use client";

import type { AmendmentFilters, SearchFilters, TextCatalogFilters } from "@democracy-watch/data";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { queryKeys } from "./keys.ts";
import { useRepository } from "./provider.tsx";

/** Recherche élargie. Garde les résultats précédents pendant qu'un filtre se recharge. */
export const useSearch = (filters: SearchFilters) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.search(filters),
    queryFn: () => repository.search(filters),
    placeholderData: keepPreviousData,
  });
};

/** Catalogue des textes à ajouter à l'étude. */
export const useTextCatalog = (filters: TextCatalogFilters) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.catalog(filters),
    queryFn: () => repository.listTexts(filters),
    placeholderData: keepPreviousData,
  });
};

/** Plusieurs textes (les textes suivis). */
export const useTexts = (ids: string[]) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.texts(ids),
    queryFn: () => repository.getTexts(ids),
    enabled: ids.length > 0,
    placeholderData: keepPreviousData,
  });
};

export const useText = (id: string) => {
  const repository = useRepository();
  return useQuery({ queryKey: queryKeys.text(id), queryFn: () => repository.getText(id) });
};

export const useArticles = (textId: string) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.articles(textId),
    queryFn: () => repository.listArticles(textId),
  });
};

/** Un article, son texte et ses amendements (vue « avancement »). */
export const useArticleView = (textId: string, articleNumber: string) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.article(textId, articleNumber),
    queryFn: () => repository.getArticleView(textId, articleNumber),
  });
};

/** Amendements des textes suivis (`filters.scope`). Vide tant qu'aucun texte n'est suivi. */
export const useAmendments = (filters: AmendmentFilters) => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.amendments(filters),
    queryFn: () => repository.listAmendments(filters),
    enabled: filters.scope.length > 0,
    placeholderData: keepPreviousData,
  });
};

export const useCommissions = () => {
  const repository = useRepository();
  return useQuery({
    queryKey: queryKeys.commissions(),
    queryFn: () => repository.listCommissions(),
    staleTime: Number.POSITIVE_INFINITY,
  });
};
