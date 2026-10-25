"use client";

import { useAmendments, useTexts } from "@democracy-watch/api";
import {
  type AmendmentResult,
  type AmendmentStatus,
  amendmentStatusLabels,
  EXAMINATION_STAGES,
  type ExaminationStage,
  examinationStageLabels,
  type GroupCode,
  type LegislativeText,
} from "@democracy-watch/data";
import { parliamentaryGroups } from "@democracy-watch/theme";
import {
  AmendmentRow,
  buildHref,
  EmptyState,
  FilterPanel,
  Link,
  PageHeader,
  type QueryParams,
  toggle,
  useNavigation,
} from "@democracy-watch/ui";
import { TextInput } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import type { FormEvent } from "react";
import classes from "../screens.module.css";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";
import { type AmendmentParams, amendmentParamsOf, parseAmendmentParams } from "./params.ts";

const STATUSES: AmendmentStatus[] = [
  "adopte",
  "rejete",
  "en-attente",
  "tombe",
  "retire",
  "non-soutenu",
  "irrecevable",
];

const NO_FILTER: AmendmentParams = { q: "", textIds: [], groups: [], statuses: [], stages: [] };

/** « Mes amendements suivis » : amendements des textes suivis, filtrables (filtres en accordéons). */
export const FollowedAmendmentsScreen = ({ params = {} }: { params?: QueryParams }) => {
  const followed = useFollowed();
  const filters = parseAmendmentParams(params);
  const amendments = useAmendments({ scope: followed.ids, ...filters });
  const all = useAmendments({ scope: followed.ids, ...NO_FILTER });
  const texts = useTexts(followed.ids);

  if (followed.ids.length === 0) {
    return (
      <>
        <PageHeader
          breadcrumb={[{ href: "/", label: "Accueil" }, { label: "Mes amendements suivis" }]}
          title="Mes amendements suivis (0)"
        />
        <EmptyState title="Aucun texte suivi">
          Les amendements apparaissent ici dès que vous suivez un texte :{" "}
          <Link href="/textes/ajouter">ajouter des textes à l'étude</Link>.
        </EmptyState>
      </>
    );
  }

  return (
    <QueryView query={amendments}>
      {(items) => (
        <AmendmentsView
          filters={filters}
          amendments={items}
          texts={texts.data ?? []}
          total={all.data?.length ?? items.length}
        />
      )}
    </QueryView>
  );
};

type AmendmentsViewProps = {
  filters: AmendmentParams;
  amendments: AmendmentResult[];
  texts: LegislativeText[];
  total: number;
};

const AmendmentsView = ({ filters, amendments, texts, total }: AmendmentsViewProps) => {
  const { navigate } = useNavigation();
  const go = (next: Partial<AmendmentParams>) =>
    navigate(buildHref("/amendements", amendmentParamsOf({ ...filters, ...next })));
  const groups = [
    ...new Set(amendments.map((amendment) => amendment.author.group).concat(filters.groups)),
  ].sort();

  const onSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = new FormData(event.currentTarget).get("q");
    go({ q: typeof q === "string" ? q.trim() : "" });
  };

  const onToggle = (groupId: string, value: string) => {
    if (groupId === "texte") go({ textIds: toggle(filters.textIds, value) });
    if (groupId === "groupe") go({ groups: toggle(filters.groups, value as GroupCode) });
    if (groupId === "statut") go({ statuses: toggle(filters.statuses, value as AmendmentStatus) });
    if (groupId === "etape") go({ stages: toggle(filters.stages, value as ExaminationStage) });
  };

  return (
    <>
      <PageHeader
        breadcrumb={[{ href: "/", label: "Accueil" }, { label: "Mes amendements suivis" }]}
        title={`Mes amendements suivis (${total})`}
      />
      <search>
        <form onSubmit={onSearch} className={classes.fullSearch}>
          <TextInput
            name="q"
            key={filters.q}
            defaultValue={filters.q}
            aria-label="Rechercher dans mes amendements suivis"
            placeholder="Rechercher un mot-clé, une tournure (« par dérogation », « le cas échéant »…), un n°, un auteur"
            leftSection={<IconSearch size={16} aria-hidden />}
          />
        </form>
      </search>
      <div className={classes.withSidebar}>
        <FilterPanel
          variant="accordion"
          onToggle={onToggle}
          onReset={() => navigate("/amendements")}
          groups={[
            {
              id: "texte",
              label: "Texte de loi",
              options: texts.map((text) => ({
                value: text.id,
                label: text.shortTitle,
                checked: filters.textIds.includes(text.id),
              })),
            },
            {
              id: "groupe",
              label: "Groupe parlementaire",
              options: groups.map((code) => ({
                value: code,
                label: `${code} · ${parliamentaryGroups[code].label}`,
                color: parliamentaryGroups[code].color,
                checked: filters.groups.includes(code),
              })),
            },
            {
              id: "statut",
              label: "Statut / sort",
              options: STATUSES.map((status) => ({
                value: status,
                label: amendmentStatusLabels[status],
                checked: filters.statuses.includes(status),
              })),
            },
            {
              id: "etape",
              label: "Étape législative",
              options: EXAMINATION_STAGES.map((stage) => ({
                value: stage,
                label: examinationStageLabels[stage],
                checked: filters.stages.includes(stage),
              })),
            },
          ]}
        />
        <div>
          <p className={classes.hint} aria-live="polite">
            {amendments.length} amendement{amendments.length > 1 ? "s" : ""} affiché
            {amendments.length > 1 ? "s" : ""}
          </p>
          {amendments.length === 0 ? (
            <EmptyState title="Aucun amendement">
              Aucun amendement suivi ne correspond à ces filtres.
            </EmptyState>
          ) : (
            <ul className={classes.list}>
              {amendments.map((amendment) => (
                <AmendmentRow key={amendment.id} amendment={amendment} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
};
