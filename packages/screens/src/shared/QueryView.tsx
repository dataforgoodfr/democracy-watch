"use client";

import { ErrorState, LoadingState } from "@democracy-watch/ui";
import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";

type QueryViewProps<T> = {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
  lines?: number;
};

/** Rend l'état d'une requête : chargement, erreur récupérable, puis les données. */
export const QueryView = <T,>({ query, children, lines }: QueryViewProps<T>) => {
  if (query.isPending) return <LoadingState lines={lines} />;
  if (query.isError) return <ErrorState onRetry={() => void query.refetch()} />;
  return <>{children(query.data)}</>;
};
