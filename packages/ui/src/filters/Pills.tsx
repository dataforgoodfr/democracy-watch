"use client";

import classes from "./filters.module.css";

export type Pill = { value: string; label: string; count?: number };

type PillsProps = {
  items: Pill[];
  /** Valeurs actives (une seule pour des onglets, plusieurs pour des chips). */
  active: readonly string[];
  onSelect: (value: string) => void;
  label: string;
};

/**
 * Pilules : onglets de type de résultat (« Tout · 128 ») ou chips de filtres (« PJL », « PPL »).
 * Chaque pilule est un bouton à bascule (aria-pressed).
 */
export const Pills = ({ items, active, onSelect, label }: PillsProps) => (
  <fieldset className={classes.pills}>
    <legend className="dw-visually-hidden">{label}</legend>
    {items.map((item) => {
      const pressed = active.includes(item.value);
      return (
        <button
          key={item.value}
          type="button"
          className={classes.pill}
          aria-pressed={pressed}
          onClick={() => onSelect(item.value)}
        >
          {item.label}
          {item.count === undefined ? null : ` · ${item.count}`}
        </button>
      );
    })}
  </fieldset>
);
