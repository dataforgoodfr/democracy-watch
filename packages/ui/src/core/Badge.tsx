import type { ReactNode } from "react";
import classes from "./core.module.css";

export type BadgeTone =
  | "neutre"
  | "info"
  | "succes"
  | "erreur"
  | "avertissement"
  | "marque"
  | "action";

type BadgeProps = {
  tone?: BadgeTone;
  icon?: ReactNode;
  size?: "sm" | "md";
  children: ReactNode;
};

/** Badge du styleguide : 12/20 gras, majuscules, rayon 4 px. La couleur n'est jamais seule. */
export const Badge = ({ tone = "neutre", icon, size = "sm", children }: BadgeProps) => (
  <span className={classes.badge} data-tone={tone} data-size={size}>
    {icon}
    {children}
  </span>
);
