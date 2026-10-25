"use client";

import { EmptyState, Link, PageHeader } from "@democracy-watch/ui";

export const NotFoundScreen = () => (
  <>
    <PageHeader title="Page introuvable" />
    <EmptyState title="Cette page n'existe pas ou a été déplacée.">
      <Link href="/">Revenir à l'accueil</Link> ou lancer une recherche.
    </EmptyState>
  </>
);
