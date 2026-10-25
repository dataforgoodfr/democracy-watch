import type {
  AmendmentFilters,
  AmendmentStatus,
  ExaminationStage,
  GroupCode,
} from "@democracy-watch/data";
import { asArray, asString, type QueryParams } from "@democracy-watch/ui";

/** Filtres de « Mes amendements suivis » (le périmètre — textes suivis — est ajouté par l'écran). */
export type AmendmentParams = Omit<AmendmentFilters, "scope">;

export const parseAmendmentParams = (params: QueryParams): AmendmentParams => ({
  q: asString(params.q).trim(),
  textIds: asArray(params.texte),
  groups: asArray(params.groupe) as GroupCode[],
  statuses: asArray(params.statut) as AmendmentStatus[],
  stages: asArray(params.etape) as ExaminationStage[],
});

export const amendmentParamsOf = (filters: AmendmentParams) => ({
  q: filters.q,
  texte: filters.textIds,
  groupe: filters.groups,
  statut: filters.statuses,
  etape: filters.stages,
});
