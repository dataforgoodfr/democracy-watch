"use client";

import { useAmendments, useRepository, useTexts } from "@democracy-watch/api";
import {
  AmendmentRow,
  Card,
  daysUntil,
  EmptyState,
  formatDate,
  Link,
  PageHeader,
  SectionHeader,
} from "@democracy-watch/ui";
import { Button } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";
import classes from "../screens.module.css";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";

const SHORTCUTS = [
  { href: "/textes/ajouter", label: "Ajouter un texte" },
  { href: "/recherche", label: "Rechercher un amendement" },
  { href: "/amendements", label: "Mes amendements suivis" },
];

const NO_FILTER = { q: "", textIds: [], groups: [], statuses: [], stages: [] };

/** Accueil connecté : échéances et derniers amendements des textes suivis, raccourcis. */
export const HomeScreen = () => {
  const today = useRepository().referenceDate();
  const followed = useFollowed();
  const texts = useTexts(followed.ids);
  const amendments = useAmendments({ scope: followed.ids, ...NO_FILTER });

  return (
    <>
      <PageHeader
        title="Votre veille"
        description={`Situation au ${formatDate(today)} : échéances et derniers amendements de vos textes.`}
      />
      {followed.ids.length === 0 ? (
        <EmptyState title="Vous ne suivez encore aucun texte">
          <p>Choisissez les textes à suivre : leurs articles et amendements apparaîtront ici.</p>
          <Button
            component={Link}
            href="/textes/ajouter"
            leftSection={<IconPlus size={18} aria-hidden />}
          >
            Ajouter des textes à l'étude
          </Button>
        </EmptyState>
      ) : (
        <>
          <div className={classes.homeGrid}>
            <section aria-labelledby="echeances">
              <QueryView query={texts} lines={2}>
                {(items) => {
                  const deadlines = items
                    .filter((text) => text.nextDeadline)
                    .sort((a, b) =>
                      (a.nextDeadline?.date ?? "").localeCompare(b.nextDeadline?.date ?? ""),
                    );
                  return (
                    <>
                      <SectionHeader
                        id="echeances"
                        title="Échéances à venir"
                        count={deadlines.length}
                      />
                      {deadlines.length === 0 ? (
                        <EmptyState>Aucune échéance annoncée pour vos textes.</EmptyState>
                      ) : (
                        <ul className={classes.list}>
                          {deadlines.map((text) => (
                            <li key={text.id} className={classes.listRow}>
                              <div>
                                <Link href={`/textes/${text.id}`} className={classes.rowLink}>
                                  {text.shortTitle}
                                </Link>
                                <p className={classes.rowText}>
                                  {text.nextDeadline?.label} ·{" "}
                                  {text.nextDeadline ? formatDate(text.nextDeadline.date) : ""}
                                </p>
                              </div>
                              {text.nextDeadline ? (
                                <strong className={classes.deadline}>
                                  J-{daysUntil(text.nextDeadline.date, today)}
                                </strong>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  );
                }}
              </QueryView>
            </section>
            <Card panel as="aside" aria-label="Raccourcis">
              <h2 className={classes.asideTitle}>Raccourcis</h2>
              <ul className={classes.shortcuts}>
                {SHORTCUTS.map((shortcut) => (
                  <li key={shortcut.href}>
                    <Link href={shortcut.href}>{shortcut.label} →</Link>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
          <section aria-labelledby="derniers" className={classes.section}>
            <SectionHeader
              id="derniers"
              title="Derniers amendements déposés"
              action={<Link href="/amendements">Tous les amendements →</Link>}
            />
            <QueryView query={amendments}>
              {(items) =>
                items.length === 0 ? (
                  <EmptyState>Aucun amendement déposé sur vos textes pour l'instant.</EmptyState>
                ) : (
                  <ul className={classes.list}>
                    {[...items]
                      .sort((a, b) => b.depositedAt.localeCompare(a.depositedAt))
                      .slice(0, 5)
                      .map((amendment) => (
                        <AmendmentRow key={amendment.id} amendment={amendment} />
                      ))}
                  </ul>
                )
              }
            </QueryView>
          </section>
        </>
      )}
    </>
  );
};
