import type { ReactNode } from "react";
import classes from "./core.module.css";

/** État vide : aucun résultat, colonne vide, périmètre non couvert. */
export const EmptyState = ({ title, children }: { title?: string; children?: ReactNode }) => (
  <div className={classes.empty} role="status">
    {title ? <p className={classes.emptyTitle}>{title}</p> : null}
    {children}
  </div>
);
