import {
  type AmendmentStatus,
  amendmentStatusLabels,
  type GroupCode,
  type Source,
  type TextType,
  textTypeLabels,
} from "@democracy-watch/data";
import { parliamentaryGroups } from "@democracy-watch/theme";
import { IconCheck } from "@tabler/icons-react";
import { Badge, type BadgeTone } from "../core/Badge.tsx";
import classes from "./legislative.module.css";

export const TextTypeBadge = ({ type }: { type: TextType }) => (
  <Badge tone="info">{textTypeLabels[type]}</Badge>
);

const statusTone: Record<AmendmentStatus, BadgeTone> = {
  "en-attente": "neutre",
  adopte: "succes",
  rejete: "erreur",
  tombe: "erreur",
  retire: "neutre",
  "non-soutenu": "neutre",
  irrecevable: "avertissement",
};

export const AmendmentStatusBadge = ({ status }: { status: AmendmentStatus }) => (
  <Badge tone={statusTone[status]}>{amendmentStatusLabels[status]}</Badge>
);

/** Commission ; avec une échéance, le badge passe en avertissement (« COMMISSION AU FOND · J-1 »). */
export const CommissionBadge = ({
  label,
  deadline,
}: {
  label: string;
  deadline?: number | null;
}) =>
  deadline === undefined || deadline === null ? (
    <Badge>{label}</Badge>
  ) : (
    <Badge tone="avertissement">
      {label} · J{deadline >= 0 ? `-${deadline}` : `+${-deadline}`}
    </Badge>
  );

export const StudyBadge = () => (
  <Badge tone="succes" icon={<IconCheck size={12} aria-hidden />}>
    À l'étude
  </Badge>
);

const sourceLabels: Record<Source, string> = {
  "assemblee-nationale": "Assemblée nationale",
  legifrance: "Légifrance · droit en vigueur",
};

export const SourceBadge = ({ source }: { source: Source }) => (
  <Badge
    tone={source === "assemblee-nationale" ? "succes" : "info"}
    icon={<IconCheck size={12} aria-hidden />}
  >
    {sourceLabels[source]}
  </Badge>
);

/** Pastille de groupe parlementaire. Toujours accompagnée du sigle (jamais la couleur seule). */
export const GroupDot = ({ code }: { code: GroupCode }) => (
  <span
    className={classes.groupDot}
    style={{ background: `var(--dw-groupe-${code.toLowerCase()})` }}
    title={parliamentaryGroups[code].label}
    aria-hidden
  />
);
