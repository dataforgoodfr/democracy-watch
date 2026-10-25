import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export type AlertKind = "amendements" | "etape" | "similaires";

/** Un texte suivi et les préférences choisies en l'ajoutant. */
export type FollowedText = {
  id: string;
  addedAt: string;
  /** « tous » ou liste de numéros d'articles. */
  articles: "tous" | string[];
  alerts: AlertKind[];
  theme: string | null;
};

type FollowState = {
  texts: FollowedText[];
  /** Ajoute (ou met à jour) des textes suivis. */
  follow: (items: FollowedText[]) => void;
  unfollow: (id: string) => void;
  clear: () => void;
};

/** Textes suivis par l'utilisateur. Persistés dans localStorage (clé `dw:suivi`). */
export const useFollowStore = create<FollowState>()(
  persist(
    (set) => ({
      texts: [],
      follow: (items) =>
        set((state) => {
          const ids = new Set(items.map((item) => item.id));
          return { texts: [...state.texts.filter((text) => !ids.has(text.id)), ...items] };
        }),
      unfollow: (id) => set((state) => ({ texts: state.texts.filter((text) => text.id !== id) })),
      clear: () => set({ texts: [] }),
    }),
    {
      name: "dw:suivi",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      // Réhydraté après le premier rendu (voir rehydrateStores) : pas d'écart avec le rendu serveur.
      skipHydration: true,
    },
  ),
);

/** Identifiants des textes suivis, dans l'ordre d'ajout. */
export const useFollowedIds = () => useFollowStore((state) => state.texts.map((text) => text.id));
