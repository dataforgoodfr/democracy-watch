import { type AmendmentView, asString, type QueryParams } from "@democracy-watch/ui";

const VIEWS: AmendmentView[] = ["liste", "avancement", "groupe"];

export type ArticleFilters = { q: string; view: AmendmentView; groupSimilar: boolean };

export const parseArticleParams = (params: QueryParams): ArticleFilters => {
  const view = asString(params.vue) as AmendmentView;
  return {
    q: asString(params.q).trim(),
    view: VIEWS.includes(view) ? view : "avancement",
    groupSimilar: asString(params.similaires) === "1",
  };
};

export const articleParamsOf = (filters: ArticleFilters) => ({
  q: filters.q,
  vue: filters.view === "avancement" ? null : filters.view,
  similaires: filters.groupSimilar ? "1" : null,
});
