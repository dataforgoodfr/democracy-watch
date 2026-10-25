import { useSyncExternalStore } from "react";
import { useFollowStore } from "./follow.ts";
import { useSessionStore } from "./session.ts";

const stores = [useFollowStore, useSessionStore];

/** Lit le stockage du navigateur. À appeler une fois, côté client, après le premier rendu. */
export const rehydrateStores = () => Promise.all(stores.map((store) => store.persist.rehydrate()));

const subscribe = (onChange: () => void) => {
  const unsubscribers = stores.map((store) => store.persist.onFinishHydration(onChange));
  return () => {
    for (const unsubscribe of unsubscribers) unsubscribe();
  };
};

const hydrated = () => stores.every((store) => store.persist.hasHydrated());

/** Vrai une fois l'état du navigateur chargé. Toujours faux pendant le rendu serveur. */
export const useStoresHydrated = () => useSyncExternalStore(subscribe, hydrated, () => false);
