import type { ZudokuConfig } from "zudoku";

type NavItem = NonNullable<ZudokuConfig["navigation"]>[number];
type Icon = NonNullable<Extract<NavItem, { type: "doc" }>["icon"]>;

const doc = (file: string, label: string, icon: Icon) => ({
  type: "doc" as const,
  file,
  path: `/${file.replace(/(\/)?index\.mdx$/, "").replace(/\.mdx$/, "")}`,
  label,
  icon,
});

export const navigation: ZudokuConfig["navigation"] = [
  doc("index.mdx", "Accueil", "home"),
  {
    type: "category",
    label: "Produit",
    icon: "lightbulb",
    items: [
      doc("00-produit/notions-metier.mdx", "Notions métier (AN)", "book-open"),
      doc("00-produit/analyse-existant.mdx", "Analyse de l'existant", "search"),
      doc("00-produit/methode-de-travail.mdx", "Méthode de travail (RFC)", "users"),
      {
        type: "doc",
        file: "00-produit/prompt-de-conception.md",
        path: "/00-produit/prompt-de-conception",
        label: "Prompt de conception",
        icon: "file-text",
      },
    ],
  },
  {
    type: "category",
    label: "Démarrer",
    icon: "rocket",
    items: [
      doc("01-demarrer/index.mdx", "Installation", "terminal"),
      doc("01-demarrer/contribuer.mdx", "Contribuer", "git-pull-request"),
      doc("01-demarrer/deploiement.mdx", "Déploiement (Coolify)", "cloud-upload"),
    ],
  },
  {
    type: "category",
    label: "Design system",
    icon: "palette",
    items: [
      doc("02-design-system/index.mdx", "Principes et règles", "scale"),
      doc("02-design-system/couleurs.mdx", "Couleurs", "droplet"),
      doc("02-design-system/typographie.mdx", "Typographie", "type"),
      doc("02-design-system/espacements.mdx", "Espacements et formes", "ruler"),
      doc("02-design-system/logo.mdx", "Logo et favicons", "eye"),
      {
        type: "category",
        label: "Composants",
        icon: "component",
        link: "02-design-system/composants/index.mdx",
        items: [
          {
            type: "category",
            label: "Fondations",
            icon: "box",
            collapsible: false,
            items: [
              doc("02-design-system/composants/badge.mdx", "Badge", "tag"),
              doc("02-design-system/composants/card.mdx", "Card", "square"),
              doc("02-design-system/composants/empty-state.mdx", "EmptyState", "inbox"),
              doc("02-design-system/composants/highlight.mdx", "Highlight", "highlighter"),
              doc("02-design-system/composants/link.mdx", "Link", "link"),
              doc("02-design-system/composants/loading-state.mdx", "LoadingState", "loader"),
              doc("02-design-system/composants/error-state.mdx", "ErrorState", "triangle-alert"),
            ],
          },
          {
            type: "category",
            label: "Mise en page",
            icon: "layout-template",
            collapsible: false,
            items: [
              doc("02-design-system/composants/app-shell.mdx", "AppShell", "layout"),
              doc("02-design-system/composants/global-search.mdx", "GlobalSearch", "search"),
              doc("02-design-system/composants/page-header.mdx", "PageHeader", "heading"),
              doc("02-design-system/composants/breadcrumb.mdx", "Breadcrumb", "chevrons-right"),
              doc("02-design-system/composants/section-header.mdx", "SectionHeader", "heading-2"),
            ],
          },
          {
            type: "category",
            label: "Filtres",
            icon: "sliders-horizontal",
            collapsible: false,
            items: [
              doc("02-design-system/composants/filter-panel.mdx", "FilterPanel", "filter"),
              doc("02-design-system/composants/pills.mdx", "Pills", "pill"),
              doc("02-design-system/composants/view-switcher.mdx", "ViewSwitcher", "columns-3"),
            ],
          },
          {
            type: "category",
            label: "Législatif",
            icon: "scale",
            collapsible: false,
            items: [
              doc("02-design-system/composants/text-type-badge.mdx", "TextTypeBadge", "file-text"),
              doc(
                "02-design-system/composants/commission-badge.mdx",
                "CommissionBadge",
                "badge-check",
              ),
              doc(
                "02-design-system/composants/amendment-status-badge.mdx",
                "AmendmentStatusBadge",
                "badge-check",
              ),
              doc("02-design-system/composants/study-badge.mdx", "StudyBadge", "badge-check"),
              doc("02-design-system/composants/source-badge.mdx", "SourceBadge", "shield-check"),
              doc("02-design-system/composants/group-dot.mdx", "GroupDot", "circle"),
              doc("02-design-system/composants/author-line.mdx", "AuthorLine", "user"),
              doc("02-design-system/composants/legal-quote.mdx", "LegalQuote", "quote"),
              doc(
                "02-design-system/composants/legislative-text-card.mdx",
                "LegislativeTextCard",
                "file-text",
              ),
              doc("02-design-system/composants/article-row.mdx", "ArticleRow", "list"),
              doc("02-design-system/composants/amendment-row.mdx", "AmendmentRow", "list"),
              doc("02-design-system/composants/amendment-card.mdx", "AmendmentCard", "file-text"),
              doc("02-design-system/composants/stage-column.mdx", "StageColumn", "columns-3"),
              doc("02-design-system/composants/legend.mdx", "Legend", "list"),
              doc("02-design-system/composants/texts-table.mdx", "TextsTable", "table"),
            ],
          },
          {
            type: "category",
            label: "Marque",
            icon: "eye",
            collapsible: false,
            items: [
              doc("02-design-system/composants/logo.mdx", "Logo", "eye"),
              doc("02-design-system/composants/picto.mdx", "Picto", "eye"),
            ],
          },
        ],
      },
    ],
  },
  {
    type: "category",
    label: "Architecture",
    icon: "layers",
    items: [
      doc("03-architecture/index.mdx", "Vue d'ensemble", "boxes"),
      doc("03-architecture/pages.mdx", "Pages et écrans", "layout-dashboard"),
      doc("03-architecture/donnees.mdx", "Données, navigation, connexion", "workflow"),
      doc("03-architecture/tests.mdx", "Tests", "flask-conical"),
    ],
  },
  {
    type: "category",
    label: "Serveur",
    icon: "server",
    link: "04-serveur/index.mdx",
    items: [doc("04-serveur/api.mdx", "API", "zap")],
  },
  doc("05-roadmap/index.mdx", "Roadmap", "map"),
];
