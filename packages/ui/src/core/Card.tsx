import type { ReactNode } from "react";
import classes from "./core.module.css";

type CardProps = {
  children: ReactNode;
  /** Panneau (rayon 16) plutôt que carte (rayon 8). */
  panel?: boolean;
  padding?: "sm" | "md";
  as?: "div" | "section" | "article" | "aside" | "li";
  "aria-label"?: string;
};

export const Card = ({
  children,
  panel = false,
  padding = "md",
  as: Tag = "div",
  ...rest
}: CardProps) => (
  <Tag className={classes.card} data-panel={panel || undefined} data-padding={padding} {...rest}>
    {children}
  </Tag>
);
