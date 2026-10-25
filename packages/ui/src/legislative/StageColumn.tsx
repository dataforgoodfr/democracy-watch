import type { ReactNode } from "react";
import { EmptyState } from "../core/EmptyState.tsx";
import classes from "./legislative.module.css";

type StageColumnProps = {
  title: string;
  subtitle: string;
  count: number;
  /** Prochaine échéance : colonne mise en avant (avertissement). */
  upcoming?: boolean;
  /** Hors périmètre (ex. Sénat en V0). */
  disabled?: boolean;
  emptyText?: string;
  /** Répartition des sorts (barre gris / vert / rouge). */
  outcomes?: { pending: number; adopted: number; rejected: number };
  children?: ReactNode;
};

/** Colonne de la vue « avancement » : une étape d'examen et ses amendements. */
export const StageColumn = ({
  title,
  subtitle,
  count,
  upcoming,
  disabled,
  emptyText,
  outcomes,
  children,
}: StageColumnProps) => {
  const total = outcomes ? outcomes.pending + outcomes.adopted + outcomes.rejected : 0;
  return (
    <section
      className={classes.column}
      data-upcoming={upcoming || undefined}
      data-disabled={disabled || undefined}
      aria-label={`${title} — ${count}`}
    >
      <header className={classes.columnHeader}>
        <h3 className={classes.columnTitle}>{title}</h3>
        <span className={classes.columnCount}>{count}</span>
      </header>
      <p className={classes.columnSubtitle}>{subtitle}</p>
      {outcomes && total > 0 ? (
        <div
          className={classes.outcomes}
          role="img"
          aria-label={`${outcomes.pending} en attente, ${outcomes.adopted} adoptés, ${outcomes.rejected} rejetés`}
        >
          <span style={{ flex: outcomes.pending }} data-kind="pending" />
          <span style={{ flex: outcomes.adopted }} data-kind="adopted" />
          <span style={{ flex: outcomes.rejected }} data-kind="rejected" />
        </div>
      ) : null}
      {count === 0 ? (
        emptyText ? (
          <EmptyState>{emptyText}</EmptyState>
        ) : null
      ) : (
        <ul className={classes.cards}>{children}</ul>
      )}
    </section>
  );
};
