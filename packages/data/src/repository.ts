/**
 * Point d'accès unique aux données. Deux implémentations respectent cette interface :
 * les données fictives (mode DEV_FRONT, tests, documentation) et l'API HTTP
 * (`@democracy-watch/api`). Les écrans n'en voient jamais la différence.
 */
import { amendments, articles, commissions, fixtureToday, texts } from "./fixtures.ts";
import {
  type AmendmentFilters,
  type AmendmentResult,
  type ArticleView,
  type Dataset,
  getArticleView,
  listAmendments,
  listTexts,
  type SearchFilters,
  type SearchResults,
  search,
  type TextCatalogFilters,
} from "./queries.ts";
import type { Article, Commission, LegislativeText, Page } from "./types.ts";

export type ArticleSummary = Article & { amendmentCount: number };

export type Repository = {
  search(filters: SearchFilters): Promise<SearchResults>;
  /** Catalogue des textes (« Ajouter des textes à l'étude »). */
  listTexts(filters: TextCatalogFilters): Promise<Page<LegislativeText>>;
  /** Textes par identifiants, dans l'ordre demandé (textes suivis). */
  getTexts(ids: string[]): Promise<LegislativeText[]>;
  getText(id: string): Promise<LegislativeText | null>;
  /** Sommaire d'un texte : ses articles et leur nombre d'amendements. */
  listArticles(textId: string): Promise<ArticleSummary[]>;
  getArticleView(textId: string, articleNumber: string): Promise<ArticleView | null>;
  listAmendments(filters: AmendmentFilters): Promise<AmendmentResult[]>;
  listCommissions(): Promise<Commission[]>;
  /** Date de référence des échéances (« J-1 ») : aujourd'hui, ou la date figée des données fictives. */
  referenceDate(): string;
};

export const fixtureDataset: Dataset = { texts, articles, amendments, commissions };

export const createFixtureRepository = (data: Dataset = fixtureDataset): Repository => ({
  search: async (filters) => search(data, filters),
  listTexts: async (filters) => listTexts(data, filters),
  getTexts: async (ids) => ids.flatMap((id) => data.texts.filter((text) => text.id === id)),
  getText: async (id) => data.texts.find((text) => text.id === id) ?? null,
  listArticles: async (textId) =>
    data.articles
      .filter((article) => article.textId === textId)
      .map((article) => ({
        ...article,
        amendmentCount: data.amendments.filter((amendment) => amendment.articleId === article.id)
          .length,
      })),
  getArticleView: async (textId, articleNumber) => getArticleView(data, textId, articleNumber),
  listAmendments: async (filters) => listAmendments(data, filters),
  listCommissions: async () => data.commissions,
  referenceDate: () => fixtureToday,
});
