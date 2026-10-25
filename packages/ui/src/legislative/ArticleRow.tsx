import type { ArticleResult } from "@democracy-watch/data";
import { Badge } from "../core/Badge.tsx";
import { Highlight } from "../core/Highlight.tsx";
import { Link } from "../core/navigation.tsx";
import { plural } from "./format.ts";
import classes from "./legislative.module.css";

/** Ligne d'article : « Art. 3 Produits phytosanitaires · PJL… », résumé, nombre d'amendements, « Ouvrir → ». */
export const ArticleRow = ({
  article,
  href,
  highlight = [],
}: {
  article: ArticleResult;
  href: string;
  highlight?: readonly string[];
}) => (
  <li className={classes.row}>
    <div className={classes.rowMain}>
      <p className={classes.rowTitle}>
        <span className={classes.mono}>Art. {article.number}</span> <strong>{article.title}</strong>{" "}
        <span className={classes.mention}>· {article.text.shortTitle}</span>
      </p>
      <p className={classes.rowText}>
        <Highlight text={article.summary} stems={highlight} />
      </p>
    </div>
    <Badge>{plural(article.amendmentCount, "amendement")}</Badge>
    <Link
      href={href}
      className={classes.open}
      aria-label={`Ouvrir l'article ${article.number} — ${article.title}`}
    >
      Ouvrir →
    </Link>
  </li>
);
