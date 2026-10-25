"use client";

import { useArticleView, useCommissions, useRepository } from "@democracy-watch/api";
import {
  type Amendment,
  type ArticleView,
  type Commission,
  EXAMINATION_STAGES,
  type ExaminationStage,
  examinationStageLabels,
  type GroupCode,
  groupByStage,
  matches,
} from "@democracy-watch/data";
import { parliamentaryGroups } from "@democracy-watch/theme";
import {
  AmendmentCard,
  AmendmentRow,
  Badge,
  buildHref,
  CommissionBadge,
  daysUntil,
  EmptyState,
  formatDate,
  GroupDot,
  Legend,
  PageHeader,
  plural,
  type QueryParams,
  StageColumn,
  useNavigation,
  ViewSwitcher,
} from "@democracy-watch/ui";
import { Switch, TextInput } from "@mantine/core";
import { IconSearch, IconStarFilled } from "@tabler/icons-react";
import type { FormEvent } from "react";
import { NotFoundScreen } from "../not-found/NotFoundScreen.tsx";
import classes from "../screens.module.css";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";
import { type ArticleFilters, articleParamsOf, parseArticleParams } from "./params.ts";

/** Amendements visibles : en mode regroupé, les similaires sont repliés dans la carte de référence. */
const visibleAmendments = (amendments: Amendment[], groupSimilar: boolean) =>
  groupSimilar
    ? amendments.filter(
        (amendment) => !amendments.some((other) => other.id === amendment.similarTo?.amendmentId),
      )
    : amendments;

type ArticleScreenProps = { textId: string; articleNumber: string; params?: QueryParams };

/** Article et ses amendements (maquette « V0 · 5 ») : vues liste, avancement, groupe parlementaire. */
export const ArticleScreen = ({ textId, articleNumber, params = {} }: ArticleScreenProps) => {
  const filters = parseArticleParams(params);
  const view = useArticleView(textId, articleNumber);
  const commissions = useCommissions();
  const today = useRepository().referenceDate();
  const followed = useFollowed();
  return (
    <QueryView query={view}>
      {(data) =>
        data ? (
          <ArticleBoard
            {...data}
            amendments={data.amendments.filter((amendment) =>
              matches(filters.q, amendment.number, amendment.author.name, amendment.summary),
            )}
            allAmendments={data.amendments}
            filters={filters}
            commissions={commissions.data ?? []}
            today={today}
            followed={followed.isFollowed(data.text.id)}
          />
        ) : (
          <NotFoundScreen />
        )
      }
    </QueryView>
  );
};

type ArticleBoardProps = ArticleView & {
  allAmendments: Amendment[];
  filters: ArticleFilters;
  commissions: Commission[];
  today: string;
  followed: boolean;
};

const ArticleBoard = ({
  text,
  article,
  amendments,
  allAmendments,
  filters,
  commissions,
  today,
  followed,
}: ArticleBoardProps) => {
  const { navigate } = useNavigation();
  const basePath = `/textes/${text.id}/articles/${article.number}`;
  const go = (next: Partial<ArticleFilters>) =>
    navigate(buildHref(basePath, articleParamsOf({ ...filters, ...next })));
  const commissionName = (id: string | null) =>
    commissions.find((commission) => commission.id === id)?.name ?? "";
  const numberOf = (id: string | undefined) =>
    allAmendments.find((amendment) => amendment.id === id)?.number;
  const deadline = text.nextDeadline ? daysUntil(text.nextDeadline.date, today) : null;
  const shown = visibleAmendments(amendments, filters.groupSimilar);

  const onSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = new FormData(event.currentTarget).get("q");
    go({ q: typeof q === "string" ? q.trim() : "" });
  };

  const card = (amendment: Amendment) => (
    <AmendmentCard
      key={amendment.id}
      amendment={amendment}
      similar={allAmendments.filter((other) => other.similarTo?.amendmentId === amendment.id)}
      similarToNumber={numberOf(amendment.similarTo?.amendmentId)}
      parentNumber={numberOf(amendment.parentId ?? undefined)}
      redepositNumber={numberOf(amendment.redepositedAs?.amendmentId)}
    />
  );

  const stageSubtitle = (stage: ExaminationStage) => {
    switch (stage) {
      case "depose":
        return "pas encore examinés";
      case "commission-fond":
        return [
          commissionName(text.leadCommissionId),
          text.nextDeadline ? formatDate(text.nextDeadline.date).replace(/ \d{4}$/, "") : null,
          deadline === null ? null : `J-${deadline}`,
        ]
          .filter(Boolean)
          .join(" · ");
      case "commission-avis":
        return (
          text.opinionCommissionIds.map(commissionName).join(", ") || "aucune commission saisie"
        );
      case "seance":
        return "date à programmer";
      case "senat":
        return "hors périmètre V0";
    }
  };

  const byStage = groupByStage(shown);
  const byGroup = Object.entries(
    shown.reduce<Record<string, Amendment[]>>((groups, amendment) => {
      groups[amendment.author.group] = [...(groups[amendment.author.group] ?? []), amendment];
      return groups;
    }, {}),
  ) as [GroupCode, Amendment[]][];

  return (
    <>
      <PageHeader
        breadcrumb={[
          { href: "/textes", label: "Mes textes de loi" },
          { href: `/textes/${text.id}`, label: text.shortTitle },
          { label: `Article ${article.number}` },
        ]}
        title={`Article ${article.number} · ${article.title}`}
        badges={
          <>
            <Badge>{plural(allAmendments.length, "amendement")}</Badge>
            {deadline === null ? null : (
              <CommissionBadge label={text.stageLabel} deadline={deadline} />
            )}
          </>
        }
        actions={
          followed ? (
            <span className={classes.followed}>
              <IconStarFilled size={16} aria-hidden /> Suivi
            </span>
          ) : null
        }
        description={article.summary}
      />
      <search>
        <form onSubmit={onSearch} className={classes.fullSearch}>
          <TextInput
            name="q"
            key={filters.q}
            defaultValue={filters.q}
            aria-label="Rechercher dans les amendements de l'article"
            placeholder="Rechercher un mot-clé, une tournure (« par dérogation », « le cas échéant »…), un n°, un auteur"
            leftSection={<IconSearch size={16} aria-hidden />}
          />
        </form>
      </search>
      <div className={classes.toolbar}>
        <ViewSwitcher value={filters.view} onChange={(view) => go({ view })} />
        <Switch
          label="Regrouper les similaires ≥ 85 %"
          checked={filters.groupSimilar}
          onChange={() => go({ groupSimilar: !filters.groupSimilar })}
        />
      </div>

      {shown.length === 0 ? (
        <EmptyState title="Aucun amendement">
          Aucun amendement ne correspond à cette recherche.
        </EmptyState>
      ) : null}

      {filters.view === "avancement" && shown.length > 0 ? (
        <>
          <div className={classes.board}>
            {EXAMINATION_STAGES.map((stage) => {
              const items = byStage.get(stage) ?? [];
              return (
                <StageColumn
                  key={stage}
                  title={examinationStageLabels[stage]}
                  subtitle={stageSubtitle(stage)}
                  count={items.length}
                  upcoming={stage === "commission-fond" && deadline !== null}
                  disabled={stage === "senat"}
                  emptyText={
                    stage === "depose"
                      ? "Aucun amendement en attente d'examen. Les nouveaux dépôts arrivent ici."
                      : stage === "seance"
                        ? "Les amendements redéposés en séance seront rattachés automatiquement à leur version de commission, quel que soit l'auteur."
                        : undefined
                  }
                  outcomes={{
                    pending: items.filter((item) => item.status === "en-attente").length,
                    adopted: items.filter((item) => item.status === "adopte").length,
                    rejected: items.filter(
                      (item) => item.status === "rejete" || item.status === "tombe",
                    ).length,
                  }}
                >
                  {items.map(card)}
                </StageColumn>
              );
            })}
          </div>
          <Legend />
        </>
      ) : null}

      {filters.view === "liste" && shown.length > 0 ? (
        <ul className={classes.list}>
          {shown.map((amendment) => (
            <AmendmentRow key={amendment.id} amendment={{ ...amendment, text, article }} />
          ))}
        </ul>
      ) : null}

      {filters.view === "groupe" && shown.length > 0 ? (
        <div className={classes.groups}>
          {byGroup.map(([code, items]) => (
            <section
              key={code}
              aria-label={parliamentaryGroups[code].label}
              className={classes.groupSection}
            >
              <h2 className={classes.groupTitle}>
                <GroupDot code={code} /> {code} · {parliamentaryGroups[code].label}{" "}
                <span className={classes.hint}>({items.length})</span>
              </h2>
              <ul className={classes.cardGrid}>{items.map(card)}</ul>
            </section>
          ))}
        </div>
      ) : null}
    </>
  );
};
