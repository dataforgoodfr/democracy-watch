import type { Amendment } from "@democracy-watch/data";
import { AmendmentStatusBadge, GroupDot } from "./badges.tsx";
import classes from "./legislative.module.css";

type AmendmentCardProps = {
  amendment: Amendment;
  /** Amendements similaires (calculé) : la carte reçoit une bordure sarcelle. */
  similar?: Amendment[];
  /** Numéro de l'amendement dont celui-ci est proche (« ≈ 88 % de CE 23 »). */
  similarToNumber?: string;
  parentNumber?: string;
  redepositNumber?: string;
};

/** Carte compacte d'amendement (vue « avancement »). Les liens calculés sont signalés comme tels. */
export const AmendmentCard = ({
  amendment,
  similar = [],
  similarToNumber,
  parentNumber,
  redepositNumber,
}: AmendmentCardProps) => {
  const grouped = similar.length > 0 || Boolean(similarToNumber);
  return (
    <li className={classes.amendmentCard} data-similar={grouped || undefined}>
      <div className={classes.cardTop}>
        <span className={classes.mono}>{amendment.number}</span>
        <AmendmentStatusBadge status={amendment.status} />
      </div>
      <p className={classes.cardAuthor}>
        <GroupDot code={amendment.author.group} />
        {amendment.author.name} · {amendment.author.group}
      </p>
      <p className={classes.cardSummary}>
        {parentNumber ? `Sous-amendement à ${parentNumber} : ` : ""}
        {amendment.summary}
      </p>
      {similar.length > 0 ? (
        <p className={classes.computed}>
          ≈ {similar.length} similaire{similar.length > 1 ? "s" : ""} ·{" "}
          {[...new Set(similar.map((item) => item.author.group))].join(", ")}
        </p>
      ) : null}
      {similarToNumber && amendment.similarTo ? (
        <p className={classes.computed}>
          ≈ {amendment.similarTo.score} % de {similarToNumber}
        </p>
      ) : null}
      {redepositNumber ? (
        <p className={classes.probable}>
          ↪ redéposé en {redepositNumber} ? <span>à vérifier</span>
        </p>
      ) : null}
    </li>
  );
};
