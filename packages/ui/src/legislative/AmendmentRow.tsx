import type { AmendmentResult } from "@democracy-watch/data";
import { Highlight } from "../core/Highlight.tsx";
import { AmendmentStatusBadge, GroupDot } from "./badges.tsx";
import classes from "./legislative.module.css";

/** « M. Garnier (RN) + 3 cosignataires » */
export const AuthorLine = ({
  amendment,
}: {
  amendment: Pick<AmendmentResult, "author" | "cosignatories">;
}) => (
  <span className={classes.author}>
    <GroupDot code={amendment.author.group} />
    {amendment.author.name} ({amendment.author.group})
    {amendment.cosignatories > 0
      ? ` + ${amendment.cosignatories} cosignataire${amendment.cosignatories > 1 ? "s" : ""}`
      : ""}
  </span>
);

/** Ligne compacte d'amendement : numéro, auteur, texte et article, résumé, statut. */
export const AmendmentRow = ({
  amendment,
  highlight = [],
}: {
  amendment: AmendmentResult;
  highlight?: readonly string[];
}) => (
  <li className={classes.row}>
    <div className={classes.rowMain}>
      <p className={classes.rowTitle}>
        <span className={classes.mono}>{amendment.number}</span>{" "}
        <AuthorLine amendment={amendment} />{" "}
        <span className={classes.mention}>
          · {amendment.text.shortTitle}
          {amendment.article ? ` · Art. ${amendment.article.number}` : ""}
          {amendment.alinea ? `, al. ${amendment.alinea}` : ""}
        </span>
      </p>
      <p className={classes.rowText}>
        <Highlight text={amendment.summary} stems={highlight} />
      </p>
    </div>
    <AmendmentStatusBadge status={amendment.status} />
  </li>
);
