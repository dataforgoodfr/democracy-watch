import { colors, radius } from "@democracy-watch/theme";
import type { ZudokuConfig } from "zudoku";
import {
  Captures,
  ColorSwatches,
  Epics,
  FeatureCard,
  FeatureGrid,
  Kanban,
  Mermaid,
  Preview,
  RadiusScale,
  SpacingScale,
  StandardizationTable,
  TypeScale,
} from "./src/components/index.ts";
import { navigation } from "./zudoku.navigation.ts";
import "./zudoku.theme.css";

/** Thème de la doc dérivé des tokens du styleguide (packages/theme) : aucune couleur en dur. */
const light = {
  background: colors["fond-surface"],
  foreground: colors["texte-defaut"],
  card: colors["fond-surface"],
  cardForeground: colors["texte-defaut"],
  popover: colors["fond-surface"],
  popoverForeground: colors["texte-defaut"],
  primary: colors["fond-action"],
  primaryForeground: colors["fond-surface"],
  secondary: colors["fond-neutre"],
  secondaryForeground: colors["texte-titre"],
  muted: colors["fond-neutre"],
  mutedForeground: colors["texte-mention"],
  accent: colors["fond-marque"],
  accentForeground: colors["texte-action"],
  destructive: colors["statut-erreur"],
  destructiveForeground: colors["fond-surface"],
  border: colors["bordure-defaut"],
  input: colors["bordure-defaut"],
  ring: colors.focus,
  radius: `${radius.md / 16}rem`,
};

/** Palette sombre : vert encre en fond, jaune clair en accent. */
const dark = {
  ...light,
  background: "#0F201D",
  foreground: "#E8F0EE",
  card: colors["fond-action"],
  cardForeground: "#E8F0EE",
  popover: colors["fond-action"],
  popoverForeground: "#E8F0EE",
  primary: colors["fond-marque"],
  primaryForeground: colors["fond-action"],
  secondary: "#21463F",
  secondaryForeground: "#E8F0EE",
  muted: "#21463F",
  mutedForeground: "#A6C4BE",
  accent: "#21463F",
  accentForeground: colors["fond-marque"],
  border: "#2A5850",
  input: "#2A5850",
};

const config: ZudokuConfig = {
  metadata: {
    title: "%s | Democracy Watch Docs",
    description:
      "Documentation technique de Democracy Watch : guide, design system, architecture et roadmap.",
    favicon: "/favicon.svg",
  },
  theme: {
    fonts: {
      sans: {
        url: "https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,500;0,700;1,800&display=swap",
        fontFamily: "Archivo",
      },
    },
    light,
    dark,
  },
  site: {
    title: "Docs",
    logo: {
      src: { light: "/logo.svg", dark: "/logo-inverse.svg" },
      alt: "Democracy Watch",
      width: 200,
      href: "/",
    },
    showPoweredBy: false,
  },
  header: {
    navigation: [
      { label: "GitHub", to: "https://github.com/dataforgoodfr/democracy-watch", target: "_blank" },
    ],
  },
  search: { type: "pagefind" },
  navigation,
  mdx: {
    components: {
      Captures,
      ColorSwatches,
      Epics,
      FeatureCard,
      FeatureGrid,
      Kanban,
      Mermaid,
      Preview,
      RadiusScale,
      SpacingScale,
      StandardizationTable,
      TypeScale,
    },
  },
  docs: {
    files: "./**/*.{md,mdx}",
    defaultOptions: { showLastModified: false },
  },
};

export default config;
