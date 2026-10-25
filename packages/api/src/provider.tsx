"use client";

import type { Repository } from "@democracy-watch/data";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, type ReactNode, useContext, useState } from "react";

const RepositoryContext = createContext<Repository | null>(null);

export const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });

type ApiProviderProps = {
  repository: Repository;
  children: ReactNode;
  /** Client fourni (tests) ; sinon un client par montage. */
  queryClient?: QueryClient;
};

/** Fournit le dépôt de données (API ou mock) et le cache TanStack Query. */
export const ApiProvider = ({ repository, children, queryClient }: ApiProviderProps) => {
  const [client] = useState(() => queryClient ?? createQueryClient());
  return (
    <QueryClientProvider client={client}>
      <RepositoryContext.Provider value={repository}>{children}</RepositoryContext.Provider>
    </QueryClientProvider>
  );
};

export const useRepository = () => {
  const repository = useContext(RepositoryContext);
  if (!repository) throw new Error("useRepository doit être utilisé sous <ApiProvider>.");
  return repository;
};
