import type { ReactNode } from "react";
import { Link } from "../core/navigation.tsx";
import classes from "./layout.module.css";

export type Crumb = { href?: string; label: string };

export const Breadcrumb = ({ items }: { items: Crumb[] }) => (
  <nav aria-label="Fil d'Ariane" className={classes.breadcrumb}>
    <ol>
      {items.map((item, index) => {
        const last = index === items.length - 1;
        return (
          <li key={`${item.href ?? "courant"}-${item.label}`}>
            {item.href && !last ? (
              <Link href={item.href}>{item.label}</Link>
            ) : (
              <span aria-current={last ? "page" : undefined}>{item.label}</span>
            )}
          </li>
        );
      })}
    </ol>
  </nav>
);

type PageHeaderProps = {
  title: ReactNode;
  breadcrumb?: Crumb[];
  description?: ReactNode;
  /** Badges affichés à côté du titre. */
  badges?: ReactNode;
  /** Actions alignées à droite (suivre, sources…). */
  actions?: ReactNode;
};

/** En-tête de page : fil d'Ariane, titre H1, badges, description et actions. */
export const PageHeader = ({
  title,
  breadcrumb,
  description,
  badges,
  actions,
}: PageHeaderProps) => (
  <div className={classes.pageHeader}>
    {breadcrumb ? <Breadcrumb items={breadcrumb} /> : null}
    <div className={classes.titleRow}>
      <div className={classes.titleGroup}>
        <h1 className={classes.title}>{title}</h1>
        {badges}
      </div>
      {actions ? <div className={classes.actions}>{actions}</div> : null}
    </div>
    {description ? <p className={classes.description}>{description}</p> : null}
  </div>
);

type SectionHeaderProps = { title: string; count?: number; action?: ReactNode; id?: string };

/** Titre de section avec compteur et lien « Voir les n → ». */
export const SectionHeader = ({ title, count, action, id }: SectionHeaderProps) => (
  <div className={classes.sectionHeader}>
    <h2 id={id} className={classes.sectionTitle}>
      {title}
      {count === undefined ? null : <span className={classes.count}>{count}</span>}
    </h2>
    {action}
  </div>
);
