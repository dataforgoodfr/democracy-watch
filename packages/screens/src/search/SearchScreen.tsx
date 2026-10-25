"use client";

import { useCommissions, useRepository, useSearch } from "@democracy-watch/api";
import {
  type Commission,
  type GroupCode,
  type SearchFilters,
  type SearchResults,
  type TextStage,
  textStageLabels,
} from "@democracy-watch/data";
import { parliamentaryGroups } from "@democracy-watch/theme";
import {
  AmendmentRow,
  ArticleRow,
  buildHref,
  daysUntil,
  EmptyState,
  FilterPanel,
  LegislativeTextCard,
  Link,
  PageHeader,
  Pills,
  type QueryParams,
  SectionHeader,
  toggle,
  useNavigation,
} from "@democracy-watch/ui";
import classes from "../screens.module.css";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";
import { parseSearchParams, searchParamsOf } from "./params.ts";

const GROUPS: GroupCode[] = [
  "ECO",
  "SOC",
  "DR",
  "RN",
  "LFI",
  "EPR",
  "DEM",
  "HOR",
  "LIOT",
  "GDR",
  "UDR",
  "NI",
];
const STAGES: TextStage[] = ["depot", "commission", "seance", "adopte"];
const PREVIEW = 5;

type SearchViewProps = {
  filters: SearchFilters;
  results: SearchResults;
  commissions: Commission[];
  today: string;
  followedIds: string[];
};

/** Recherche élargie (maquette « V0 · 1 ») : textes, articles et amendements. */
export const SearchScreen = ({ params = {} }: { params?: QueryParams }) => {
  const followed = useFollowed();
  const filters = { ...parseSearchParams(params), followedIds: followed.ids };
  const search = useSearch(filters);
  const commissions = useCommissions();
  const today = useRepository().referenceDate();
  return (
    <QueryView query={search}>
      {(results) => (
        <SearchView
          filters={filters}
          results={results}
          commissions={commissions.data ?? []}
          today={today}
          followedIds={followed.ids}
        />
      )}
    </QueryView>
  );
};

const SearchView = ({ filters, results, commissions, today, followedIds }: SearchViewProps) => {
  const { navigate } = useNavigation();
  const go = (next: Partial<SearchFilters>) =>
    navigate(buildHref("/recherche", searchParamsOf({ ...filters, ...next })));
  const commissionName = (id: string) =>
    commissions.find((commission) => commission.id === id)?.name ?? id;
  const show = (tab: SearchFilters["tab"]) => filters.tab === "tout" || filters.tab === tab;
  const limit = <T,>(items: T[]) => (filters.tab === "tout" ? items.slice(0, PREVIEW) : items);
  const tabHref = (tab: SearchFilters["tab"]) =>
    buildHref("/recherche", searchParamsOf({ ...filters, tab }));

  const onToggle = (groupId: string, value: string) => {
    if (groupId === "suivis") go({ onlyFollowed: !filters.onlyFollowed });
    if (groupId === "etape") go({ stages: toggle(filters.stages, value as TextStage) });
    if (groupId === "commission") go({ commissions: toggle(filters.commissions, value) });
    if (groupId === "groupe") go({ groups: toggle(filters.groups, value as GroupCode) });
  };

  return (
    <>
      <PageHeader
        breadcrumb={[{ href: "/", label: "Accueil" }, { label: "Recherche" }]}
        title={
          filters.q
            ? `${results.counts.tout} résultats pour « ${filters.q} »`
            : `${results.counts.tout} résultats`
        }
        description="Dans les textes de loi, leurs articles et les amendements déposés · Assemblée nationale · XVIIe législature"
      />
      <div className={classes.toolbar}>
        <Pills
          label="Type de résultat"
          active={[filters.tab]}
          onSelect={(tab) => go({ tab: tab as SearchFilters["tab"] })}
          items={[
            { value: "tout", label: "Tout", count: results.counts.tout },
            { value: "textes", label: "Textes de loi", count: results.counts.textes },
            { value: "articles", label: "Articles", count: results.counts.articles },
            { value: "amendements", label: "Amendements", count: results.counts.amendements },
          ]}
        />
        <p className={classes.hint}>Synonymes inclus ✓ · Tri : pertinence</p>
      </div>
      <div className={classes.withSidebar}>
        <FilterPanel
          onToggle={onToggle}
          onReset={() => navigate(buildHref("/recherche", { q: filters.q }))}
          groups={[
            {
              id: "suivis",
              label: "Mes textes",
              options: [
                {
                  value: "1",
                  label: "Uniquement mes textes à l'étude",
                  checked: filters.onlyFollowed,
                },
              ],
            },
            {
              id: "etape",
              label: "Étape du texte",
              options: STAGES.map((stage) => ({
                value: stage,
                label: textStageLabels[stage],
                checked: filters.stages.includes(stage),
              })),
            },
            {
              id: "commission",
              label: "Commission",
              options: commissions.slice(0, 4).map((commission) => ({
                value: commission.id,
                label: commission.name,
                checked: filters.commissions.includes(commission.id),
              })),
            },
            {
              id: "groupe",
              label: "Groupe parlementaire (amendements)",
              options: GROUPS.slice(0, 6).map((code) => ({
                value: code,
                label: code,
                color: parliamentaryGroups[code].color,
                checked: filters.groups.includes(code),
              })),
            },
          ]}
        />
        <div className={classes.stack}>
          {results.counts.tout === 0 ? (
            <EmptyState title="Aucun résultat">
              Essayez un autre mot-clé ou{" "}
              <Link href={buildHref("/recherche", { q: filters.q })}>
                réinitialisez les filtres
              </Link>
              .
            </EmptyState>
          ) : null}
          {show("textes") && results.texts.length > 0 ? (
            <section aria-labelledby="resultats-textes">
              <SectionHeader
                id="resultats-textes"
                title="Textes de loi"
                count={results.counts.textes}
                action={
                  filters.tab === "tout" ? (
                    <Link href={tabHref("textes")}>Voir les {results.counts.textes} →</Link>
                  ) : null
                }
              />
              <div className={classes.stack}>
                {limit(results.texts).map((text) => (
                  <LegislativeTextCard
                    key={text.id}
                    text={text}
                    href={`/textes/${text.id}`}
                    commissionName={commissionName(text.leadCommissionId)}
                    highlight={results.highlight}
                    followed={followedIds.includes(text.id)}
                    deadlineIn={text.nextDeadline ? daysUntil(text.nextDeadline.date, today) : null}
                  />
                ))}
              </div>
            </section>
          ) : null}
          {show("articles") && results.articles.length > 0 ? (
            <section aria-labelledby="resultats-articles">
              <SectionHeader
                id="resultats-articles"
                title="Articles"
                count={results.counts.articles}
                action={
                  filters.tab === "tout" ? (
                    <Link href={tabHref("articles")}>Voir les {results.counts.articles} →</Link>
                  ) : null
                }
              />
              <ul className={classes.list}>
                {limit(results.articles).map((article) => (
                  <ArticleRow
                    key={article.id}
                    article={article}
                    href={`/textes/${article.textId}/articles/${article.number}`}
                    highlight={results.highlight}
                  />
                ))}
              </ul>
            </section>
          ) : null}
          {show("amendements") && results.amendments.length > 0 ? (
            <section aria-labelledby="resultats-amendements">
              <SectionHeader
                id="resultats-amendements"
                title="Amendements"
                count={results.counts.amendements}
                action={
                  filters.tab === "tout" ? (
                    <Link href={tabHref("amendements")}>
                      Voir les {results.counts.amendements} →
                    </Link>
                  ) : null
                }
              />
              <ul className={classes.list}>
                {limit(results.amendments).map((amendment) => (
                  <AmendmentRow
                    key={amendment.id}
                    amendment={amendment}
                    highlight={results.highlight}
                  />
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
};
