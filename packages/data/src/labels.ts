/** Libellés français des valeurs du domaine. */
import type { AmendmentStatus, ExaminationStage, TextStage, TextType } from "./types.ts";

export const textTypeLabels: Record<TextType, string> = {
  PJL: "Projet de loi",
  PPL: "Proposition de loi",
  PLF: "Projet de loi de finances",
  PLFSS: "Projet de loi de financement de la Sécurité sociale",
};

export const textStageLabels: Record<TextStage, string> = {
  depot: "Dépôt",
  commission: "En commission",
  seance: "En séance",
  adopte: "Adopté / promulgué",
};

export const examinationStageLabels: Record<ExaminationStage, string> = {
  depose: "Déposés",
  "commission-fond": "Commission au fond",
  "commission-avis": "Commission pour avis",
  seance: "Séance publique",
  senat: "Sénat",
};

export const amendmentStatusLabels: Record<AmendmentStatus, string> = {
  "en-attente": "En attente",
  adopte: "Adopté",
  rejete: "Rejeté",
  tombe: "Tombé",
  retire: "Retiré",
  "non-soutenu": "Non soutenu",
  irrecevable: "Irrecevable",
};
