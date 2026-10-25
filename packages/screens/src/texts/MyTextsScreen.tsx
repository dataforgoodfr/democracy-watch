"use client";

import { useCommissions, useRepository, useTexts } from "@democracy-watch/api";
import { useFollowStore } from "@democracy-watch/state";
import { daysUntil, EmptyState, LegislativeTextCard, Link, PageHeader } from "@democracy-watch/ui";
import { Button } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";
import classes from "../screens.module.css";
import { commissionNamer } from "../shared/commissions.ts";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";

/** « Mes textes de loi » : les textes suivis, choisis dans « Ajouter des textes ». */
export const MyTextsScreen = () => {
  const today = useRepository().referenceDate();
  const followed = useFollowed();
  const unfollow = useFollowStore((state) => state.unfollow);
  const texts = useTexts(followed.ids);
  const commissionName = commissionNamer(useCommissions().data);

  return (
    <>
      <PageHeader
        breadcrumb={[{ href: "/", label: "Accueil" }, { label: "Mes textes de loi" }]}
        title={`Mes textes de loi (${followed.ids.length})`}
        description="Les textes que vous suivez, mis à jour chaque jour depuis les sources officielles."
        actions={
          <Button
            component={Link}
            href="/textes/ajouter"
            leftSection={<IconPlus size={18} aria-hidden />}
          >
            Ajouter des textes
          </Button>
        }
      />
      {followed.ids.length === 0 ? (
        <EmptyState title="Aucun texte suivi">
          <Link href="/textes/ajouter">Ajoutez vos premiers textes à l'étude</Link>.
        </EmptyState>
      ) : (
        <QueryView query={texts}>
          {(items) => (
            <div className={classes.stack}>
              {items.map((text) => (
                <LegislativeTextCard
                  key={text.id}
                  text={text}
                  followed
                  href={`/textes/${text.id}`}
                  commissionName={commissionName(text.leadCommissionId)}
                  deadlineIn={text.nextDeadline ? daysUntil(text.nextDeadline.date, today) : null}
                  actions={
                    <>
                      <Button
                        component={Link}
                        href={`/textes/${text.id}`}
                        size="xs"
                        variant="light"
                      >
                        Voir les articles
                      </Button>
                      <Button
                        size="xs"
                        variant="subtle"
                        color="red"
                        onClick={() => unfollow(text.id)}
                      >
                        Ne plus suivre
                      </Button>
                    </>
                  }
                />
              ))}
            </div>
          )}
        </QueryView>
      )}
    </>
  );
};
