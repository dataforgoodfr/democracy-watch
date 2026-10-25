/**
 * Tokens du styleguide Democracy Watch (Figma « Styleguide V1 — Fondations »).
 *
 * Source unique : le CSS (`tokens.css`, généré par `pnpm --filter @democracy-watch/theme generate`),
 * le thème Mantine, la documentation et les assets de marque en dérivent.
 * En code, on utilise les tokens sémantiques (`--dw-fond-…`, `--dw-texte-…`), jamais les hex.
 */

/** Palette brute : couleurs de marque, neutres et statuts DSFR. */
export const palette = {
  "vert-900": "#17322E",
  "jaune-100": "#F5FAC4",
  "jaune-300": "#EDF58A",
  "jaune-50": "#F7FBDD",
  "sarcelle-500": "#2E9F92",
  "sarcelle-700": "#1F6F66",
  "sarcelle-50": "#E3F4F1",
  "gris-50": "#161616",
  "gris-200": "#3A3A3A",
  "gris-425": "#666666",
  "gris-900": "#DDDDDD",
  "gris-950": "#EEEEEE",
  "gris-975": "#F6F6F6",
  blanc: "#FFFFFF",
  erreur: "#CE0500",
  "erreur-fond": "#FFE9E9",
  succes: "#18753C",
  "succes-fond": "#B8FEC9",
  avertissement: "#B34000",
  "avertissement-fond": "#FFE9E6",
  info: "#0063CB",
  "info-fond": "#E8EDFF",
  focus: "#0A76F6",
} as const;

export type PaletteName = keyof typeof palette;

/** Tokens sémantiques : le rôle d'une couleur, pas sa valeur. */
export const colors = {
  "fond-action": palette["vert-900"],
  "texte-action": palette["vert-900"],
  "bordure-action": palette["vert-900"],
  "fond-marque": palette["jaune-100"],
  "texte-inverse": palette["jaune-100"],
  "fond-marque-accent": palette["jaune-300"],
  "jaune-50": palette["jaune-50"],
  "sarcelle-500": palette["sarcelle-500"],
  "texte-accent": palette["sarcelle-700"],
  "fond-selection": palette["sarcelle-50"],
  "texte-titre": palette["gris-50"],
  "texte-defaut": palette["gris-200"],
  "texte-mention": palette["gris-425"],
  "bordure-forte": palette["gris-425"],
  "bordure-defaut": palette["gris-900"],
  "fond-neutre": palette["gris-950"],
  "fond-page": palette["gris-975"],
  "fond-surface": palette.blanc,
  "statut-erreur": palette.erreur,
  "statut-erreur-fond": palette["erreur-fond"],
  "statut-succes": palette.succes,
  "statut-succes-fond": palette["succes-fond"],
  "statut-avertissement": palette.avertissement,
  "statut-avertissement-fond": palette["avertissement-fond"],
  "statut-info": palette.info,
  "statut-info-fond": palette["info-fond"],
  focus: palette.focus,
} as const;

export type ColorToken = keyof typeof colors;

/**
 * Couleurs des groupes parlementaires (XVIIe législature), pour les pastilles et la data-viz.
 * `source: "maquette"` = relevée dans les wireframes ; `"proposition"` = à valider avec le design.
 * Jamais utilisées seules : toujours accompagnées du sigle du groupe.
 */
export const parliamentaryGroups = {
  RN: { label: "Rassemblement national", color: "#1D2B6B", source: "maquette" },
  EPR: { label: "Ensemble pour la République", color: "#8C5CC4", source: "proposition" },
  LFI: { label: "La France insoumise", color: "#E91D27", source: "maquette" },
  SOC: { label: "Socialistes et apparentés", color: "#E2457A", source: "maquette" },
  DR: { label: "Droite républicaine", color: "#2340B8", source: "maquette" },
  ECO: { label: "Écologiste et social", color: "#2E9E4F", source: "maquette" },
  DEM: { label: "Les Démocrates", color: "#F08A24", source: "maquette" },
  HOR: { label: "Horizons & indépendants", color: "#2F7FC1", source: "maquette" },
  LIOT: {
    label: "Libertés, indépendants, outre-mer et territoires",
    color: "#C49A00",
    source: "proposition",
  },
  GDR: { label: "Gauche démocrate et républicaine", color: "#A50F1F", source: "proposition" },
  UDR: { label: "Union des droites pour la République", color: "#5B3A29", source: "proposition" },
  NI: { label: "Non inscrits", color: "#929292", source: "proposition" },
} as const;

export type ParliamentaryGroupCode = keyof typeof parliamentaryGroups;

export const fonts = {
  interface: '"Archivo", arial, sans-serif',
  loi: '"Spectral", georgia, serif',
  code: 'ui-monospace, "SFMono-Regular", Menlo, monospace',
} as const;

type TextStyle = {
  size: number;
  lineHeight: number;
  weight: 400 | 500 | 700 | 800;
  mobile?: { size: number; lineHeight: number };
  family?: "interface" | "loi";
  italic?: boolean;
  uppercase?: boolean;
};

/** Échelle typographique (px). Les titres réduisent sous 768 px. */
export const typeScale = {
  h1: { size: 40, lineHeight: 48, weight: 700, mobile: { size: 32, lineHeight: 40 } },
  h2: { size: 32, lineHeight: 40, weight: 700, mobile: { size: 28, lineHeight: 36 } },
  h3: { size: 28, lineHeight: 36, weight: 700, mobile: { size: 24, lineHeight: 32 } },
  h4: { size: 24, lineHeight: 32, weight: 700, mobile: { size: 22, lineHeight: 28 } },
  h5: { size: 20, lineHeight: 28, weight: 700 },
  h6: { size: 18, lineHeight: 24, weight: 700 },
  chapo: { size: 20, lineHeight: 32, weight: 400 },
  lg: { size: 18, lineHeight: 28, weight: 400 },
  md: { size: 16, lineHeight: 24, weight: 400 },
  sm: { size: 14, lineHeight: 24, weight: 400 },
  xs: { size: 12, lineHeight: 20, weight: 400 },
  badge: { size: 12, lineHeight: 20, weight: 700, uppercase: true },
  loi: { size: 16, lineHeight: 28, weight: 400, family: "loi" },
  citation: { size: 18, lineHeight: 30, weight: 400, family: "loi", italic: true },
  logo: { size: 26, lineHeight: 28, weight: 800, italic: true },
} as const satisfies Record<string, TextStyle>;

/** Grille de 4 px (1v = 4 px). Padding et gap n'utilisent que ces valeurs. */
export const spacing = {
  "1v": 4,
  "2v": 8,
  "3v": 12,
  "4v": 16,
  "6v": 24,
  "8v": 32,
  "10v": 40,
  "12v": 48,
  "16v": 64,
} as const;

/** Rayons : les champs restent carrés (DSFR), les surfaces s'arrondissent doucement. */
export const radius = {
  aucun: 0,
  sm: 4,
  md: 8,
  lg: 16,
  xl: 28,
  pilule: 999,
} as const;

/** Traits complets (`border: var(--dw-trait-defaut)`), accent, ombre et focus. */
export const effects = {
  "trait-defaut": `1px solid ${colors["bordure-defaut"]}`,
  "trait-fort": `1px solid ${colors["bordure-forte"]}`,
  "trait-action": `1px solid ${colors["bordure-action"]}`,
  "accent-bas": `inset 0 -4px 0 ${colors["bordure-action"]}`,
  "ombre-elevee": "0 6px 18px rgba(0, 0, 18, 0.16)",
  "focus-outline": `2px solid ${colors.focus}`,
  "focus-offset": "2px",
} as const;

/** Points de rupture (px). */
export const breakpoints = { mobile: 576, tablette: 768, desktop: 1024, large: 1440 } as const;

/** Largeur maximale du contenu applicatif. */
export const contentMaxWidth = 1344;

/**
 * Écarts entre les wireframes et le styleguide, et la règle retenue.
 * Le styleguide fait foi : ce tableau est affiché dans la documentation.
 */
export const standardization = [
  {
    sujet: "Couleur d'action (boutons, onglet actif, cases cochées)",
    maquette: "Bleu DSFR #000091",
    regle: "Vert encre #17322E — --dw-fond-action",
  },
  { sujet: "Police d'interface", maquette: "Poppins", regle: "Archivo — --dw-police-interface" },
  {
    sujet: "Termes recherchés surlignés",
    maquette: "#00706F souligné",
    regle: "Sarcelle texte #1F6F66, gras souligné — --dw-texte-accent",
  },
  {
    sujet: "Bordure « groupe d'amendements similaires »",
    maquette: "Cyan #2FD3D2",
    regle: "Sarcelle #2E9F92 (décoratif autorisé) — --dw-sarcelle-500",
  },
  {
    sujet: "Colonne « prochaine échéance »",
    maquette: "Fond et bordure orange #FBBF5E",
    regle: "Avertissement #B34000 sur fond #FFE9E6 — --dw-statut-avertissement(-fond)",
  },
  {
    sujet: "Ligne survolée / sélectionnée",
    maquette: "Bleu pâle #DAE6F2",
    regle: "Sarcelle pâle #E3F4F1 — --dw-fond-selection",
  },
  {
    sujet: "En-têtes d'accordéon de filtres",
    maquette: "Lavande",
    regle: "Jaune pâle #F7FBDD — --dw-jaune-50",
  },
  {
    sujet: "Badge de commission (ex. « Affaires économiques »)",
    maquette: "Violet #6E445A",
    regle: "Neutre : texte #3A3A3A sur #EEEEEE — --dw-fond-neutre",
  },
  {
    sujet: "Header",
    maquette: "Jaune pâle, logo sur pastille jaune vif",
    regle: "Jaune clair #F5FAC4 — --dw-fond-marque ; logo vert encre",
  },
  {
    sujet: "Alinéa juridique",
    maquette: "Prompt : Spectral 18/28",
    regle: "Spectral 16/28 — .dw-loi",
  },
  {
    sujet: "Rayon des cartes",
    maquette: "Prompt : 16 px",
    regle: "8 px (--dw-rayon-md) ; 16 px réservé aux panneaux",
  },
  {
    sujet: "Onglet « Overview »",
    maquette: "Overview / Accueil",
    regle: "« Accueil » : interface 100 % en français",
  },
] as const;
