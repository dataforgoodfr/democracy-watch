import { ApiProvider, createMockRepository, createQueryClient } from "@democracy-watch/api";
import { rehydrateStores, useFollowStore, useSessionStore } from "@democracy-watch/state";
import { renderWithProviders } from "@democracy-watch/ui/test-utils";
import { act } from "@testing-library/react";
import type { ReactElement } from "react";

type ScreenOptions = { pathname?: string; followed?: string[]; signedIn?: boolean };

/**
 * Rendu d'un écran pour les tests : API en mode mock (sans latence), cache neuf, état client
 * contrôlé (textes suivis, session) et navigation simulée (URL visitées dans `visited`).
 */
export const renderScreen = async (
  ui: ReactElement,
  { pathname = "/", followed = [], signedIn = true }: ScreenOptions = {},
) => {
  localStorage.clear();
  sessionStorage.clear();
  await act(() => rehydrateStores());
  useFollowStore.setState({
    texts: followed.map((id) => ({
      id,
      addedAt: "2026-10-20T10:00:00.000Z",
      articles: "tous" as const,
      alerts: [],
      theme: null,
    })),
  });
  useSessionStore.setState({
    session: signedIn
      ? { email: "asso@example.org", remember: false, startedAt: "2026-10-20T10:00:00.000Z" }
      : null,
  });
  const queryClient = createQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, staleTime: Number.POSITIVE_INFINITY } });
  return renderWithProviders(
    <ApiProvider repository={createMockRepository({ latencyMs: 0 })} queryClient={queryClient}>
      {ui}
    </ApiProvider>,
    { pathname },
  );
};
