import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useFollowStore } from "./follow.ts";
import { rehydrateStores, useStoresHydrated } from "./hydration.ts";
import { useSessionStore } from "./session.ts";

const followed = (id: string) => ({
  id,
  addedAt: "2026-10-20T10:00:00.000Z",
  articles: "tous" as const,
  alerts: [],
  theme: null,
});

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useFollowStore.setState({ texts: [] });
  useSessionStore.setState({ session: null });
});

describe("textes suivis", () => {
  it("ajoute sans doublon et persiste dans localStorage", () => {
    useFollowStore.getState().follow([followed("pjl-2436"), followed("ppl-2511")]);
    useFollowStore.getState().follow([followed("pjl-2436")]);
    expect(useFollowStore.getState().texts.map((text) => text.id)).toEqual([
      "ppl-2511",
      "pjl-2436",
    ]);
    expect(localStorage.getItem("dw:suivi")).toContain("ppl-2511");
  });

  it("retire un texte", () => {
    useFollowStore.getState().follow([followed("pjl-2436")]);
    useFollowStore.getState().unfollow("pjl-2436");
    expect(useFollowStore.getState().texts).toEqual([]);
  });

  it("se recharge depuis le navigateur", async () => {
    localStorage.setItem(
      "dw:suivi",
      JSON.stringify({ state: { texts: [followed("ppl-2390")] }, version: 1 }),
    );
    await rehydrateStores();
    expect(useFollowStore.getState().texts.map((text) => text.id)).toEqual(["ppl-2390"]);
  });
});

describe("session", () => {
  it("sans « rester connecté » : sessionStorage uniquement", () => {
    useSessionStore.getState().signIn("asso@example.org", false);
    expect(sessionStorage.getItem("dw:session")).toContain("asso@example.org");
    expect(localStorage.getItem("dw:session")).toBeNull();
  });

  it("avec « rester connecté » : localStorage, et sessionStorage est vidé", () => {
    useSessionStore.getState().signIn("asso@example.org", false);
    useSessionStore.getState().signIn("asso@example.org", true);
    expect(localStorage.getItem("dw:session")).toContain("asso@example.org");
    expect(sessionStorage.getItem("dw:session")).toBeNull();
  });

  it("la déconnexion efface la session", () => {
    useSessionStore.getState().signIn("asso@example.org", true);
    useSessionStore.getState().signOut();
    expect(useSessionStore.getState().session).toBeNull();
  });
});

describe("hydratation", () => {
  it("signale la fin du chargement de l'état", async () => {
    const { result } = renderHook(() => useStoresHydrated());
    await act(() => rehydrateStores());
    expect(result.current).toBe(true);
  });
});
