/**
 * Modèle du domaine vu par le front. Il reprend le vocabulaire de l'Assemblée nationale
 * (dossier législatif, article, alinéa, amendement) et le modèle de la base (dump CLAIR).
 */

export type TextType = "PJL" | "PPL" | "PLF" | "PLFSS";

/** Étape du texte dans son parcours. */
export type TextStage = "depot" | "commission" | "seance" | "adopte";

/** Étape d'examen d'un amendement (colonnes de la vue « avancement »). */
export type ExaminationStage =
  | "depose"
  | "commission-fond"
  | "commission-avis"
  | "seance"
  | "senat";

/** Sort d'un amendement. Voir la doc « Notions métier » pour la définition de chaque état. */
export type AmendmentStatus =
  | "en-attente"
  | "adopte"
  | "rejete"
  | "tombe"
  | "retire"
  | "non-soutenu"
  | "irrecevable";

export type GroupCode =
  | "RN"
  | "EPR"
  | "LFI"
  | "SOC"
  | "DR"
  | "ECO"
  | "DEM"
  | "HOR"
  | "LIOT"
  | "GDR"
  | "UDR"
  | "NI";

/** Origine d'une donnée : toujours affichée, jamais implicite. */
export type Provenance = "officiel" | "reformule" | "calcule" | "probable";

export type Source = "assemblee-nationale" | "legifrance";

export type Commission = { id: string; name: string };

export type Deadline = { label: string; date: string };

export type LegislativeText = {
  id: string;
  type: TextType;
  number: number;
  title: string;
  /** Titre court utilisé dans les fils d'Ariane et les métadonnées. */
  shortTitle: string;
  depositedAt: string;
  stage: TextStage;
  /** Libellé de l'étape en cours, tel qu'affiché (« Commission au fond »). */
  stageLabel: string;
  stageDetail: string;
  leadCommissionId: string;
  opinionCommissionIds: string[];
  /** Rapporteur ou auteur principal (« rapp. Mme Petit », « M. Roux (ECO) »). */
  carriedBy: string;
  articleCount: number | null;
  amendmentCount: number;
  nextDeadline: Deadline | null;
  theme: string | null;
  /** Extrait représentatif du dispositif, utilisé par la recherche. */
  excerpt: { text: string; reference: string } | null;
};

export type Article = {
  id: string;
  textId: string;
  /** Numéro affiché : « 3 », « 1er ». */
  number: string;
  title: string;
  /** Résumé en langage clair (provenance : reformulé). */
  summary: string;
};

export type Author = { name: string; group: GroupCode };

export type Amendment = {
  id: string;
  /** Numéro affiché : « CE 23 » (commission), « CD 14 », « 1203 » (séance). */
  number: string;
  textId: string;
  articleId: string;
  alinea: number | null;
  author: Author;
  cosignatories: number;
  /** Résumé en langage clair (provenance : reformulé). */
  summary: string;
  status: AmendmentStatus;
  stage: ExaminationStage;
  commissionId: string | null;
  depositedAt: string;
  /** Sous-amendement : numéro de l'amendement parent. */
  parentId: string | null;
  /** Appartenance à un groupe d'amendements similaires (calculé). */
  similarTo: { amendmentId: string; score: number } | null;
  /** Redéposé à l'étape suivante sous un autre numéro (lien calculé, à confirmer s'il est probable). */
  redepositedAs: { amendmentId: string; certainty: "certain" | "probable" } | null;
};

export type Page<T> = { items: T[]; total: number; page: number; pageCount: number };
