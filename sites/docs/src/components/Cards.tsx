import type { ReactNode } from "react";

export const FeatureGrid = ({ children, cols = 3 }: { children: ReactNode; cols?: 2 | 3 }) => (
  <div
    className="dw-grid"
    style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${cols === 2 ? 280 : 220}px, 1fr))` }}
  >
    {children}
  </div>
);

type FeatureCardProps = { title: string; description: string; href: string; icon?: string };

export const FeatureCard = ({ title, description, href, icon }: FeatureCardProps) => (
  <a className="dw-feature" href={href}>
    {icon ? <span aria-hidden>{icon}</span> : null}
    <h3>{title}</h3>
    <p>{description}</p>
  </a>
);
