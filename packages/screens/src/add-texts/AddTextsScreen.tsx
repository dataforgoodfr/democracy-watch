"use client";

import { useCommissions, useTextCatalog } from "@democracy-watch/api";
import type { LegislativeText, TextType } from "@democracy-watch/data";
import { type AlertKind, useFollowStore } from "@democracy-watch/state";
import {
  buildHref,
  Card,
  PageHeader,
  Pills,
  type QueryParams,
  SourceBadge,
  TextsTable,
  toggle,
  useNavigation,
} from "@democracy-watch/ui";
import { Button, Checkbox, Pagination, Select, TextInput } from "@mantine/core";
import { IconSearch, IconX } from "@tabler/icons-react";
import { type FormEvent, useState } from "react";
import classes from "../screens.module.css";
import { commissionNamer } from "../shared/commissions.ts";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";
import {
  type AddTextsFilters,
  addTextsParamsOf,
  PAGE_SIZE,
  parseAddTextsParams,
} from "./params.ts";

const ALERTS: { value: AlertKind; label: string }[] = [
  { value: "amendements", label: "nouveaux amendements déposés" },
  { value: "etape", label: "le texte change d'étape" },
  { value: "similaires", label: "un amendement similaire apparaît ailleurs" },
];

/**
 * Ajouter des textes à l'étude (maquette « V0 · 2 ») : tableau + panneau « Ma sélection ».
 * Valider enregistre les textes suivis et leurs préférences dans le navigateur.
 */
export const AddTextsScreen = ({ params = {} }: { params?: QueryParams }) => {
  const { navigate } = useNavigation();
  const filters = parseAddTextsParams(params);
  const catalog = useTextCatalog({ ...filters, pageSize: PAGE_SIZE });
  const commissionName = commissionNamer(useCommissions().data);
  const followed = useFollowed();
  const follow = useFollowStore((state) => state.follow);
  const pageItems = catalog.data?.items ?? [];
  // La sélection garde les textes eux-mêmes : elle survit à la pagination et aux filtres.
  const [selected, setSelected] = useState<LegislativeText[]>([]);
  const [allArticles, setAllArticles] = useState(true);
  const [alerts, setAlerts] = useState<AlertKind[]>(["amendements", "etape"]);
  const [theme, setTheme] = useState<string | null>("Agriculture & pesticides");

  const go = (next: Partial<AddTextsFilters>) =>
    navigate(buildHref("/textes/ajouter", addTextsParamsOf({ ...filters, page: 1, ...next })));
  const selectedIds = selected.map((text) => text.id);
  const toggleText = (id: string) => {
    const text = pageItems.find((item) => item.id === id);
    if (!text) return;
    setSelected((current) =>
      selectedIds.includes(id) ? current.filter((item) => item.id !== id) : [...current, text],
    );
  };

  const onSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = new FormData(event.currentTarget).get("q");
    go({ q: typeof q === "string" ? q.trim() : "" });
  };

  const onSubmit = () => {
    const addedAt = new Date().toISOString();
    follow(
      selected.map((text) => ({
        id: text.id,
        addedAt,
        articles: allArticles ? "tous" : [],
        alerts,
        theme,
      })),
    );
    navigate("/textes");
  };

  return (
    <>
      <PageHeader
        breadcrumb={[
          { href: "/textes", label: "Mes textes de loi" },
          { label: "Ajouter des textes" },
        ]}
        title="Ajouter des textes à l'étude"
        description="Choisissez les textes en cours d'examen à suivre. Chaque texte reste relié à sa source officielle."
        actions={
          <>
            <span className={classes.hint}>Sources :</span>
            <SourceBadge source="assemblee-nationale" />
            <SourceBadge source="legifrance" />
          </>
        }
      />
      <div className={classes.withAside}>
        <Card padding="sm">
          <div className={classes.toolbar}>
            <search className={classes.inlineSearch}>
              <form onSubmit={onSearch}>
                <TextInput
                  name="q"
                  key={filters.q}
                  defaultValue={filters.q}
                  aria-label="Filtrer par mot-clé, n° de texte, rapporteur"
                  placeholder="Filtrer par mot-clé, n° de texte, rapporteur…"
                  leftSection={<IconSearch size={16} aria-hidden />}
                />
              </form>
            </search>
            <Pills
              label="Filtres rapides"
              active={[...(filters.inProgressOnly ? ["encours"] : []), ...filters.types]}
              onSelect={(value) =>
                value === "encours"
                  ? go({ inProgressOnly: !filters.inProgressOnly })
                  : go({ types: toggle(filters.types, value as TextType) })
              }
              items={[
                { value: "encours", label: "En cours d'examen" },
                { value: "PJL", label: "PJL" },
                { value: "PPL", label: "PPL" },
                { value: "PLF", label: "PLF" },
                { value: "PLFSS", label: "PLFSS" },
              ]}
            />
          </div>
          <QueryView query={catalog}>
            {(page) => (
              <>
                <TextsTable
                  texts={page.items}
                  commissionName={commissionName}
                  selected={selectedIds}
                  followedIds={followed.ids}
                  onToggle={toggleText}
                />
                <div className={classes.tableFooter}>
                  <span className={classes.hint}>
                    {page.items.length} textes sur {page.total}
                    {filters.inProgressOnly ? " en cours d'examen" : ""}
                  </span>
                  {page.pageCount > 1 ? (
                    <Pagination
                      total={page.pageCount}
                      value={page.page}
                      onChange={(next) => go({ page: next })}
                      size="sm"
                    />
                  ) : null}
                </div>
              </>
            )}
          </QueryView>
        </Card>
        <Card panel as="aside" aria-label="Ma sélection">
          <h2 className={classes.asideTitle}>
            Ma sélection · {selected.length} texte{selected.length > 1 ? "s" : ""}
          </h2>
          <ul className={classes.selection}>
            {selected.map((text) => (
              <li key={text.id}>
                <div>
                  <strong>{text.shortTitle}</strong>
                  <span className={classes.hint}>
                    {text.articleCount ?? "–"} articles · {text.amendmentCount} amendements
                  </span>
                </div>
                <button
                  type="button"
                  className={classes.iconButton}
                  aria-label={`Retirer ${text.shortTitle} de la sélection`}
                  onClick={() =>
                    setSelected((current) => current.filter((item) => item.id !== text.id))
                  }
                >
                  <IconX size={16} aria-hidden />
                </button>
              </li>
            ))}
          </ul>
          <fieldset className={classes.fieldset}>
            <legend>Articles à suivre</legend>
            <Pills
              label="Articles à suivre"
              active={[allArticles ? "tous" : "choix"]}
              onSelect={(value) => setAllArticles(value === "tous")}
              items={[
                { value: "tous", label: "Tous les articles" },
                { value: "choix", label: "Je choisis" },
              ]}
            />
          </fieldset>
          <fieldset className={classes.fieldset}>
            <legend>M'alerter quand…</legend>
            {ALERTS.map((alert) => (
              <Checkbox
                key={alert.value}
                label={alert.label}
                checked={alerts.includes(alert.value)}
                onChange={() => setAlerts((current) => toggle(current, alert.value))}
              />
            ))}
          </fieldset>
          <Select
            label="Ranger dans ma thématique"
            data={["Agriculture & pesticides", "Eau", "Santé environnementale"]}
            value={theme}
            onChange={setTheme}
            mb="lg"
          />
          <Button size="md" disabled={selected.length === 0} onClick={onSubmit}>
            Ajouter {selected.length} texte{selected.length > 1 ? "s" : ""} à mon étude
          </Button>
          <p className={classes.hint}>
            Ils apparaîtront dans « Mes textes de loi » avec leurs articles et amendements, mis à
            jour chaque jour.
          </p>
        </Card>
      </div>
    </>
  );
};
