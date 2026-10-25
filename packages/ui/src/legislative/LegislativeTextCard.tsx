import type { LegislativeText } from "@democracy-watch/data";
import type { ReactNode } from "react";
import { Link } from "../core/navigation.tsx";
import { CommissionBadge, StudyBadge, TextTypeBadge } from "./badges.tsx";
import { formatDate, plural } from "./format.ts";
import { LegalQuote } from "./LegalQuote.tsx";
import classes from "./legislative.module.css";

type LegislativeTextCardProps = {
  text: LegislativeText;
  commissionName: string;
  href: string;
  highlight?: readonly string[];
  /** Jours avant la prochaine échéance, si elle existe. */
  deadlineIn?: number | null;
  /** Le texte est suivi par l'utilisateur : badge « À l'étude ». */
  followed?: boolean;
  /** Actions affichées sous la carte (suivre, ne plus suivre…). */
  actions?: ReactNode;
};

/** Carte d'un texte de loi (résultat de recherche, liste « Mes textes de loi »). */
export const LegislativeTextCard = ({
  text,
  commissionName,
  href,
  highlight = [],
  deadlineIn,
  followed = false,
  actions,
}: LegislativeTextCardProps) => (
  <article className={classes.textCard}>
    <div className={classes.badges}>
      <TextTypeBadge type={text.type} />
      <CommissionBadge label={commissionName} />
      {deadlineIn === undefined || deadlineIn === null ? null : (
        <CommissionBadge label={text.stageLabel} deadline={deadlineIn} />
      )}
      {followed ? (
        <span className={classes.push}>
          <StudyBadge />
        </span>
      ) : null}
    </div>
    <h3 className={classes.cardTitle}>
      <Link href={href}>{text.title}</Link>
    </h3>
    {text.excerpt ? (
      <LegalQuote
        text={text.excerpt.text}
        reference={text.excerpt.reference}
        highlight={highlight}
      />
    ) : null}
    <p className={classes.meta}>
      {text.type} n° {text.number} ·{" "}
      {text.type === "PJL" || text.type === "PLF" ? "déposé" : "déposée"} le{" "}
      {formatDate(text.depositedAt)}
      {text.articleCount === null ? null : ` · ${plural(text.articleCount, "article")}`} ·{" "}
      {plural(text.amendmentCount, "amendement")}
    </p>
    {actions ? <div className={classes.cardActions}>{actions}</div> : null}
  </article>
);
