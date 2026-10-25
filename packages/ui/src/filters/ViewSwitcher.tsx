"use client";

import { SegmentedControl } from "@mantine/core";
import { IconChartPie, IconLayoutKanban, IconList } from "@tabler/icons-react";
import classes from "./filters.module.css";

export type AmendmentView = "liste" | "avancement" | "groupe";

const VIEWS: { value: AmendmentView; label: string; Icon: typeof IconList }[] = [
  { value: "liste", label: "Liste", Icon: IconList },
  { value: "avancement", label: "Avancement", Icon: IconLayoutKanban },
  { value: "groupe", label: "Groupe parlementaire", Icon: IconChartPie },
];

/** Sélecteur de vue des amendements : liste, avancement, groupe parlementaire. */
export const ViewSwitcher = ({
  value,
  onChange,
}: {
  value: AmendmentView;
  onChange: (view: AmendmentView) => void;
}) => (
  <SegmentedControl
    value={value}
    color="vert"
    onChange={(next) => onChange(next as AmendmentView)}
    aria-label="Vue des amendements"
    classNames={{ root: classes.segmented }}
    data={VIEWS.map(({ value: view, label, Icon }) => ({
      value: view,
      label: (
        <span className={classes.segmentLabel}>
          <Icon size={16} aria-hidden />
          {label}
        </span>
      ),
    }))}
  />
);
