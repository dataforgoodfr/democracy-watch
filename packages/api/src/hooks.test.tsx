import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useAmendments, useArticleView, useTexts } from "./hooks.ts";
import { createMockRepository } from "./mock.ts";
import { ApiProvider, createQueryClient } from "./provider.tsx";

const wrapper = ({ children }: { children: ReactNode }) => (
  <ApiProvider
    repository={createMockRepository({ latencyMs: 0 })}
    queryClient={createQueryClient()}
  >
    {children}
  </ApiProvider>
);

describe("hooks TanStack Query (mode DEV_FRONT)", () => {
  it("charge la vue d'un article", async () => {
    const { result } = renderHook(() => useArticleView("pjl-2436", "3"), { wrapper });
    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.amendments).toHaveLength(8);
  });

  it("ne lance pas de requête sans texte suivi", () => {
    const { result } = renderHook(
      () => useAmendments({ scope: [], q: "", textIds: [], groups: [], statuses: [], stages: [] }),
      { wrapper },
    );
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("charge les textes suivis dans l'ordre", async () => {
    const { result } = renderHook(() => useTexts(["ppl-2511", "pjl-2436"]), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.map((text) => text.id)).toEqual(["ppl-2511", "pjl-2436"]);
  });
});
