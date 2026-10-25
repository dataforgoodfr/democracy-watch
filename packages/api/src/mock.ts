import {
  createFixtureRepository,
  type Dataset,
  fixtureDataset,
  type Repository,
} from "@democracy-watch/data";

/**
 * Dépôt du mode DEV_FRONT : données fictives des maquettes, avec un délai réseau simulé
 * pour que les états de chargement restent visibles pendant le développement.
 */
export const createMockRepository = ({
  latencyMs = 300,
  data = fixtureDataset,
}: {
  latencyMs?: number;
  data?: Dataset;
} = {}): Repository => {
  const fixtures = createFixtureRepository(data);
  const delayed =
    <A extends unknown[], R>(call: (...args: A) => Promise<R>) =>
    async (...args: A) => {
      if (latencyMs > 0) await new Promise((resolve) => setTimeout(resolve, latencyMs));
      return call(...args);
    };
  return {
    search: delayed(fixtures.search),
    listTexts: delayed(fixtures.listTexts),
    getTexts: delayed(fixtures.getTexts),
    getText: delayed(fixtures.getText),
    listArticles: delayed(fixtures.listArticles),
    getArticleView: delayed(fixtures.getArticleView),
    listAmendments: delayed(fixtures.listAmendments),
    listCommissions: delayed(fixtures.listCommissions),
    referenceDate: fixtures.referenceDate,
  };
};
