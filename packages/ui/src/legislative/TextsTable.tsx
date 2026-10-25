"use client";

import type { LegislativeText } from "@democracy-watch/data";
import { Checkbox, Table } from "@mantine/core";
import { IconCheck } from "@tabler/icons-react";
import classes from "./legislative.module.css";

type TextsTableProps = {
  texts: LegislativeText[];
  commissionName: (id: string) => string;
  selected: readonly string[];
  /** Textes déjà suivis : affichés cochés, non sélectionnables. */
  followedIds?: readonly string[];
  onToggle: (id: string) => void;
};

/** Tableau de sélection des textes à suivre. Les textes déjà à l'étude ne sont pas sélectionnables. */
export const TextsTable = ({
  texts,
  commissionName,
  selected,
  followedIds = [],
  onToggle,
}: TextsTableProps) => (
  <Table.ScrollContainer minWidth={760}>
    <Table className={classes.table} verticalSpacing="md" highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>
            <span className="dw-visually-hidden">Sélection</span>
          </Table.Th>
          <Table.Th>Texte</Table.Th>
          <Table.Th>Étape actuelle</Table.Th>
          <Table.Th>Commission au fond</Table.Th>
          <Table.Th>Articles</Table.Th>
          <Table.Th>Amendements</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {texts.map((text) => {
          const isSelected = selected.includes(text.id);
          const followed = followedIds.includes(text.id);
          return (
            <Table.Tr key={text.id} data-selected={isSelected || undefined}>
              <Table.Td>
                {followed ? (
                  <IconCheck size={18} className={classes.followed} aria-label="Déjà à l'étude" />
                ) : (
                  <Checkbox
                    checked={isSelected}
                    onChange={() => onToggle(text.id)}
                    aria-label={`Sélectionner ${text.title}`}
                  />
                )}
              </Table.Td>
              <Table.Td>
                <strong className={classes.tableTitle}>{text.title}</strong>
                <span className={classes.mention}>
                  {text.type} n° {text.number} · {text.carriedBy}
                  {followed ? " · déjà à l'étude" : ""}
                </span>
              </Table.Td>
              <Table.Td>
                <span className={text.nextDeadline ? classes.stageUpcoming : undefined}>
                  {text.stageLabel}
                </span>
                <span className={classes.mention}>{text.stageDetail}</span>
              </Table.Td>
              <Table.Td>{commissionName(text.leadCommissionId)}</Table.Td>
              <Table.Td>{text.articleCount ?? "–"}</Table.Td>
              <Table.Td>{text.amendmentCount}</Table.Td>
            </Table.Tr>
          );
        })}
      </Table.Tbody>
    </Table>
  </Table.ScrollContainer>
);
