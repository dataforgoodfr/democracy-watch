import { create } from "zustand";
import { createJSONStorage, persist, type StateStorage } from "zustand/middleware";

/** Session de démonstration (V0) : pas d'authentification réelle, voir la doc « Connexion ». */
export type Session = {
  email: string;
  remember: boolean;
  startedAt: string;
};

type SessionState = {
  session: Session | null;
  signIn: (email: string, remember: boolean) => void;
  signOut: () => void;
};

const browser = () => typeof window !== "undefined";

/**
 * « Rester connecté » coché → localStorage (survit à la fermeture du navigateur) ;
 * sinon → sessionStorage (oubliée à la fermeture de l'onglet).
 */
const sessionStorageChoice: StateStorage = {
  getItem: (name) =>
    browser() ? (sessionStorage.getItem(name) ?? localStorage.getItem(name)) : null,
  setItem: (name, value) => {
    if (!browser()) return;
    const remember = (JSON.parse(value) as { state?: { session?: Session | null } }).state?.session
      ?.remember;
    const [target, other] = remember
      ? [localStorage, sessionStorage]
      : [sessionStorage, localStorage];
    target.setItem(name, value);
    other.removeItem(name);
  },
  removeItem: (name) => {
    if (!browser()) return;
    sessionStorage.removeItem(name);
    localStorage.removeItem(name);
  },
};

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      session: null,
      signIn: (email, remember) =>
        set({ session: { email, remember, startedAt: new Date().toISOString() } }),
      signOut: () => set({ session: null }),
    }),
    {
      name: "dw:session",
      version: 1,
      storage: createJSONStorage(() => sessionStorageChoice),
      skipHydration: true,
    },
  ),
);
