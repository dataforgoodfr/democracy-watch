"use client";

import { Accordion, Checkbox } from "@mantine/core";
import classes from "./filters.module.css";

export type FilterOption = { value: string; label: string; checked: boolean; color?: string };

export type FilterGroup = { id: string; label: string; options: FilterOption[] };

type FilterPanelProps = {
  groups: FilterGroup[];
  onToggle: (groupId: string, value: string) => void;
  onReset: () => void;
  /** « panel » : bloc à titres (recherche) ; « accordion » : sections repliables (amendements suivis). */
  variant?: "panel" | "accordion";
  title?: string;
};

const Options = ({
  group,
  onToggle,
}: {
  group: FilterGroup;
  onToggle: FilterPanelProps["onToggle"];
}) => (
  <div className={classes.options}>
    {group.options.map((option) => (
      <Checkbox
        key={option.value}
        checked={option.checked}
        onChange={() => onToggle(group.id, option.value)}
        label={
          option.color ? (
            <span className={classes.withDot}>
              <span className={classes.dot} style={{ background: option.color }} aria-hidden />
              {option.label}
            </span>
          ) : (
            option.label
          )
        }
      />
    ))}
  </div>
);

/** Panneau de filtres à cases à cocher, avec « Réinitialiser ». */
export const FilterPanel = ({
  groups,
  onToggle,
  onReset,
  variant = "panel",
  title = "Filtres",
}: FilterPanelProps) => (
  <section className={classes.panel} data-variant={variant} aria-label={title}>
    <div className={classes.panelHeader}>
      <h2 className={classes.panelTitle}>{title}</h2>
      <button type="button" className={classes.reset} onClick={onReset}>
        Réinitialiser
      </button>
    </div>
    {variant === "accordion" ? (
      <Accordion
        multiple
        defaultValue={groups.map((group) => group.id)}
        classNames={{ control: classes.accordionControl }}
      >
        {groups.map((group) => (
          <Accordion.Item key={group.id} value={group.id}>
            <Accordion.Control>{group.label}</Accordion.Control>
            <Accordion.Panel>
              <Options group={group} onToggle={onToggle} />
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    ) : (
      groups.map((group) => (
        <fieldset key={group.id} className={classes.group}>
          <legend className={classes.legend}>{group.label}</legend>
          <Options group={group} onToggle={onToggle} />
        </fieldset>
      ))
    )}
  </section>
);
