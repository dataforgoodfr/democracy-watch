"use client";

import { Button, TextInput } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import type { FormEvent } from "react";
import { buildHref } from "../core/href.ts";
import { useNavigation } from "../core/navigation.tsx";
import classes from "./layout.module.css";

/**
 * Recherche globale. C'est un vrai formulaire GET vers /recherche : il fonctionne aussi sans JavaScript.
 */
export const GlobalSearch = ({ defaultValue = "" }: { defaultValue?: string }) => {
  const { navigate } = useNavigation();
  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = new FormData(event.currentTarget).get("q");
    navigate(buildHref("/recherche", { q: typeof q === "string" ? q.trim() : "" }));
  };
  return (
    <search className={classes.searchLandmark}>
      <form action="/recherche" method="get" onSubmit={onSubmit} className={classes.search}>
        <TextInput
          name="q"
          key={defaultValue}
          defaultValue={defaultValue}
          aria-label="Rechercher un texte de loi, un amendement, un article"
          placeholder="Rechercher un texte de loi, un amendement, un article"
          classNames={{ root: classes.searchField, input: classes.searchInput }}
        />
        <Button
          type="submit"
          size="md"
          leftSection={<IconSearch size={20} aria-hidden />}
          className={classes.searchButton}
        >
          Rechercher
        </Button>
      </form>
    </search>
  );
};
