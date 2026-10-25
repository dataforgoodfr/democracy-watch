/**
 * Roadmap de Democracy Watch : épiques (grandes structures thématiques) et tickets.
 *
 * Source de vérité : une fiche Markdown par ticket dans `06-roadmap/04-issues/<épique>/`,
 * `06-roadmap/05-analytics/` ou `06-roadmap/06-observability/`.
 * Son frontmatter (`id`, `epic`, `status`, `size`, `v0`, `github`, `depends_on`, `note`) est lu par
 * scripts/generate-roadmap.mjs, qui produit issues.generated.json (lancé avant `dev` et `build`).
 * Ajouter un ticket = ajouter une fiche.
 */
import generated from "./issues.generated.json";

export const STATUSES = [
  "Backlog",
  "Not Started",
  "To Implement",
  "In Progress",
  "In Testing",
  "In Review",
  "Done",
] as const;
export type Status = (typeof STATUSES)[number];

/** Signification de chaque colonne (identique dans le GitHub Project). */
export const STATUS_HELP: Record<Status, string> = {
  Backlog: "Idée ou besoin identifié, pas encore priorisé",
  "Not Started": "Priorisé et prêt (description, critères), personne dessus",
  "To Implement": "Pris en charge et prêt à être réalisé, pas encore commencé",
  "In Progress": "En cours de réalisation",
  "In Testing": "Réalisé, en recette (tests, accessibilité, données réelles)",
  "In Review": "Pull request ouverte ou branche à relire",
  Done: "Fusionné sur main ou terminé",
};

export type Board = "produit-front" | "data-ops";

export type Epic = {
  id: string;
  title: string;
  board: Board;
  /** Issue chapeau GitHub correspondante, si elle existe. */
  github?: number;
  goal: string;
};

export const EPICS: Epic[] = [
  {
    id: "E1",
    title: "Produit et design",
    board: "produit-front",
    github: 1,
    goal: "Comprendre les associations et figer les maquettes",
  },
  {
    id: "E2",
    title: "Suivre des textes",
    board: "produit-front",
    github: 14,
    goal: "Choisir ses textes et les retrouver",
  },
  {
    id: "E3",
    title: "Kanban des amendements",
    board: "produit-front",
    github: 15,
    goal: "Voir où en est chaque amendement d'un article",
  },
  {
    id: "E4",
    title: "Comprendre un amendement",
    board: "produit-front",
    github: 16,
    goal: "Lire son contenu exact et son parcours",
  },
  {
    id: "E5",
    title: "Être prévenu",
    board: "produit-front",
    goal: "Savoir ce qui a changé depuis la dernière visite",
  },
  {
    id: "E6",
    title: "Comptes et ouverture",
    board: "produit-front",
    goal: "Travailler à plusieurs, ouvrir le service",
  },
  {
    id: "E7",
    title: "Données et API",
    board: "data-ops",
    github: 8,
    goal: "Les vrais textes de la XVIIe législature, servis par l'API",
  },
  {
    id: "E8",
    title: "Ops, qualité et déploiement",
    board: "data-ops",
    goal: "Mettre en ligne, sécuriser, garantir la qualité",
  },
  {
    id: "E9",
    title: "Analytics",
    board: "data-ops",
    goal: "Savoir si le service est utilisé, sans cookie ni service tiers (Rybbit)",
  },
  {
    id: "E10",
    title: "Observabilité",
    board: "data-ops",
    goal: "Savoir quand ça casse et pourquoi (OpenObserve, OpenTelemetry)",
  },
];

export type Size = "S" | "M" | "L";

export type Issue = {
  /** `DW-NN` pour la roadmap, `#NN` pour une issue GitHub existante. */
  id: string;
  title: string;
  epic: string;
  status: Status;
  size?: Size;
  /** Nécessaire pour la V0 du 7 novembre 2026. */
  v0?: boolean;
  /** Issue GitHub qui porte (ou portera) ce travail. */
  github?: number;
  dependsOn?: string[];
  note?: string;
  /** URL de la fiche dans la documentation. */
  path: string;
};

/** Index généré par scripts/generate-roadmap.mjs depuis les fiches (voir l'en-tête). */
export const ISSUES = generated as Issue[];

export const issueById = (id: string) => ISSUES.find((issue) => issue.id === id);

export const epicOf = (issue: Issue) => EPICS.find((epic) => epic.id === issue.epic);

export const issuesOfBoard = (board: Board) =>
  ISSUES.filter((issue) => epicOf(issue)?.board === board);

export const githubUrl = (number: number) =>
  `https://github.com/dataforgoodfr/democracy-watch/issues/${number}`;
