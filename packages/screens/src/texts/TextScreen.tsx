"use client";

import { useArticles, useCommissions, useText } from "@democracy-watch/api";
import { useFollowStore } from "@democracy-watch/state";
import {
  Badge,
  CommissionBadge,
  EmptyState,
  Link,
  PageHeader,
  plural,
  SectionHeader,
  StudyBadge,
  TextTypeBadge,
} from "@democracy-watch/ui";
import { Button } from "@mantine/core";
import { IconStar, IconStarFilled } from "@tabler/icons-react";
import { NotFoundScreen } from "../not-found/NotFoundScreen.tsx";
import classes from "../screens.module.css";
import { commissionNamer } from "../shared/commissions.ts";
import { QueryView } from "../shared/QueryView.tsx";
import { useFollowed } from "../shared/useFollowed.ts";

/** Fiche texte : étape, commissions et sommaire des articles ; suivre / ne plus suivre. */
export const TextScreen = ({ textId }: { textId: string }) => {
  const text = useText(textId);
  const articles = useArticles(textId);
  const commissionName = commissionNamer(useCommissions().data);
  const followed = useFollowed();
  const { follow, unfollow } = useFollowStore();

  return (
    <QueryView query={text}>
      {(data) => {
        if (!data) return <NotFoundScreen />;
        const isFollowed = followed.isFollowed(data.id);
        return (
          <>
            <PageHeader
              breadcrumb={[
                { href: "/textes", label: "Mes textes de loi" },
                { label: data.shortTitle },
              ]}
              title={data.title}
              badges={
                <>
                  <TextTypeBadge type={data.type} />
                  <CommissionBadge label={commissionName(data.leadCommissionId)} />
                  {isFollowed ? <StudyBadge /> : null}
                </>
              }
              description={[
                `${data.type} n° ${data.number}`,
                data.stageLabel,
                data.stageDetail,
                data.carriedBy,
              ]
                .filter(Boolean)
                .join(" · ")}
              actions={
                <Button
                  variant={isFollowed ? "light" : "filled"}
                  leftSection={
                    isFollowed ? (
                      <IconStarFilled size={16} aria-hidden />
                    ) : (
                      <IconStar size={16} aria-hidden />
                    )
                  }
                  onClick={() =>
                    isFollowed
                      ? unfollow(data.id)
                      : follow([
                          {
                            id: data.id,
                            addedAt: new Date().toISOString(),
                            articles: "tous",
                            alerts: ["amendements", "etape"],
                            theme: null,
                          },
                        ])
                  }
                >
                  {isFollowed ? "Suivi" : "Suivre ce texte"}
                </Button>
              }
            />
            <section aria-labelledby="sommaire">
              <QueryView query={articles}>
                {(items) => (
                  <>
                    <SectionHeader id="sommaire" title="Articles" count={items.length} />
                    {items.length === 0 ? (
                      <EmptyState>
                        Les articles de ce texte ne sont pas encore disponibles.
                      </EmptyState>
                    ) : (
                      <ul className={classes.list}>
                        {items.map((article) => (
                          <li key={article.id} className={classes.listRow}>
                            <div>
                              <Link
                                href={`/textes/${data.id}/articles/${article.number}`}
                                className={classes.rowLink}
                              >
                                Art. {article.number} · {article.title}
                              </Link>
                              <p className={classes.rowText}>{article.summary}</p>
                            </div>
                            <Badge>{plural(article.amendmentCount, "amendement")}</Badge>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                )}
              </QueryView>
            </section>
          </>
        );
      }}
    </QueryView>
  );
};
