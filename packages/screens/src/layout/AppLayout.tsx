"use client";

import { useAmendments } from "@democracy-watch/api";
import { useSessionStore, useStoresHydrated } from "@democracy-watch/state";
import { AppShell, buildHref, LoadingState, useNavigation } from "@democracy-watch/ui";
import { Button } from "@mantine/core";
import { IconLogout } from "@tabler/icons-react";
import { type ReactNode, useEffect } from "react";
import classes from "../screens.module.css";
import { useFollowed } from "../shared/useFollowed.ts";

const NO_FILTER = { q: "", textIds: [], groups: [], statuses: [], stages: [] };

/**
 * Cadre de toutes les pages connectées. Sans session, renvoie vers /connexion
 * (V0 : session de démonstration, voir la doc « Connexion »).
 */
export const AppLayout = ({ children }: { children: ReactNode }) => {
  const { navigate, pathname } = useNavigation();
  const hydrated = useStoresHydrated();
  const session = useSessionStore((state) => state.session);
  const signOut = useSessionStore((state) => state.signOut);
  const followed = useFollowed();
  const amendments = useAmendments({ scope: followed.ids, ...NO_FILTER });

  useEffect(() => {
    if (hydrated && !session) navigate(buildHref("/connexion", { suite: pathname }));
  }, [hydrated, session, navigate, pathname]);

  return (
    <AppShell
      nav={[
        { href: "/", label: "Accueil" },
        { href: "/textes", label: "Mes textes de loi", count: followed.ids.length },
        {
          href: "/amendements",
          label: "Mes amendements suivis",
          count: followed.ids.length === 0 ? 0 : (amendments.data?.length ?? undefined),
        },
      ]}
      account={
        session ? (
          <>
            <span className={classes.accountEmail}>{session.email}</span>
            <Button
              variant="subtle"
              size="xs"
              leftSection={<IconLogout size={16} aria-hidden />}
              onClick={() => {
                signOut();
                navigate("/connexion");
              }}
            >
              Se déconnecter
            </Button>
          </>
        ) : null
      }
    >
      {hydrated && session ? children : <LoadingState label="Chargement de votre espace…" />}
    </AppShell>
  );
};
