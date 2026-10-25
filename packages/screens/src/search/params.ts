import type { GroupCode, SearchFilters, SearchTab, TextStage } from "@democracy-watch/data";
import { asArray, asString, type QueryParams } from "@democracy-watch/ui";

const TABS: SearchTab[] = ["tout", "textes", "articles", "amendements"];

/** Paramètres d'URL → filtres de recherche (les textes suivis sont ajoutés par l'écran). */
export const parseSearchParams = (params: QueryParams): SearchFilters => {
  const tab = asString(params.type) as SearchTab;
  return {
    q: asString(params.q).trim(),
    tab: TABS.includes(tab) ? tab : "tout",
    onlyFollowed: asString(params.suivis) === "1",
    followedIds: [],
    stages: asArray(params.etape) as TextStage[],
    commissions: asArray(params.commission),
    groups: asArray(params.groupe) as GroupCode[],
    since: asString(params.depuis) || null,
  };
};

/** Filtres → paramètres d'URL (inverse de parseSearchParams). */
export const searchParamsOf = (filters: SearchFilters) => ({
  q: filters.q,
  type: filters.tab === "tout" ? null : filters.tab,
  suivis: filters.onlyFollowed ? "1" : null,
  etape: filters.stages,
  commission: filters.commissions,
  groupe: filters.groups,
  depuis: filters.since,
});
