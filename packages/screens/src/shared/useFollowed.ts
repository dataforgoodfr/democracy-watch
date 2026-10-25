"use client";

import { useFollowStore, useStoresHydrated } from "@democracy-watch/state";
import { useMemo } from "react";

/** Textes suivis (état du navigateur). `ready` : faux tant que le stockage n'est pas lu. */
export const useFollowed = () => {
  const ready = useStoresHydrated();
  const texts = useFollowStore((state) => state.texts);
  const ids = useMemo(() => texts.map((text) => text.id), [texts]);
  return { ready, texts, ids, isFollowed: (id: string) => ids.includes(id) };
};
