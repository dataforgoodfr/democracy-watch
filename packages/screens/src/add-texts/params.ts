import type { TextType } from "@democracy-watch/data";
import { asArray, asString, type QueryParams } from "@democracy-watch/ui";

export type AddTextsFilters = {
  q: string;
  types: TextType[];
  inProgressOnly: boolean;
  page: number;
};

export const PAGE_SIZE = 5;

export const parseAddTextsParams = (params: QueryParams): AddTextsFilters => ({
  q: asString(params.q).trim(),
  types: asArray(params.type) as TextType[],
  inProgressOnly: asString(params.encours) !== "0",
  page: Math.max(1, Number.parseInt(asString(params.page), 10) || 1),
});

export const addTextsParamsOf = (filters: AddTextsFilters) => ({
  q: filters.q,
  type: filters.types,
  encours: filters.inProgressOnly ? null : "0",
  page: filters.page > 1 ? filters.page : null,
});
