import { type CSSVariablesResolver, createTheme, type MantineColorsTuple } from "@mantine/core";
import { breakpoints, colors, fonts, palette, radius, spacing, typeScale } from "./tokens.ts";

const px = (value: number) => `${value / 16}rem`;

/** Teintes du vert encre ; l'index 9 est la couleur d'action du styleguide. */
const vert: MantineColorsTuple = [
  "#E8F0EE",
  "#CFE0DC",
  "#A6C4BE",
  "#7CA8A0",
  "#558C83",
  "#3A7067",
  "#2A5850",
  "#21463F",
  "#1B3B35",
  palette["vert-900"],
];

const sarcelle: MantineColorsTuple = [
  palette["sarcelle-50"],
  "#C2E7E1",
  "#97D6CC",
  "#6BC4B7",
  "#47B3A4",
  palette["sarcelle-500"],
  "#268A7F",
  palette["sarcelle-700"],
  "#185A53",
  "#11443F",
];

const heading = (style: { size: number; lineHeight: number }) => ({
  fontSize: px(style.size),
  lineHeight: `${style.lineHeight / style.size}`,
});

/** Thème Mantine construit sur les tokens. */
export const theme = createTheme({
  primaryColor: "vert",
  primaryShade: 9,
  colors: { vert, sarcelle },
  black: colors["texte-defaut"],
  white: colors["fond-surface"],
  fontFamily: fonts.interface,
  fontFamilyMonospace: fonts.code,
  headings: {
    fontFamily: fonts.interface,
    fontWeight: "700",
    sizes: {
      h1: heading(typeScale.h1),
      h2: heading(typeScale.h2),
      h3: heading(typeScale.h3),
      h4: heading(typeScale.h4),
      h5: heading(typeScale.h5),
      h6: heading(typeScale.h6),
    },
  },
  fontSizes: {
    xs: px(typeScale.xs.size),
    sm: px(typeScale.sm.size),
    md: px(typeScale.md.size),
    lg: px(typeScale.lg.size),
    xl: px(typeScale.chapo.size),
  },
  lineHeights: { xs: "1.67", sm: "1.71", md: "1.5", lg: "1.56", xl: "1.6" },
  spacing: {
    xs: px(spacing["2v"]),
    sm: px(spacing["3v"]),
    md: px(spacing["4v"]),
    lg: px(spacing["6v"]),
    xl: px(spacing["8v"]),
  },
  radius: {
    xs: px(radius.sm),
    sm: px(radius.sm),
    md: px(radius.md),
    lg: px(radius.lg),
    xl: px(radius.xl),
  },
  defaultRadius: "sm",
  breakpoints: {
    xs: px(breakpoints.mobile),
    sm: px(breakpoints.tablette),
    md: px(breakpoints.desktop),
    lg: px(1280),
    xl: px(breakpoints.large),
  },
  focusRing: "auto",
  cursorType: "pointer",
  components: {
    // Champs carrés, comme le DSFR.
    TextInput: { defaultProps: { radius: 0 } },
    Select: { defaultProps: { radius: 0 } },
    Checkbox: { defaultProps: { radius: 2 } },
  },
});

/** Aligne les variables Mantine sur les tokens (texte, bordures, fond). */
export const cssVariablesResolver: CSSVariablesResolver = () => ({
  variables: {},
  light: {
    "--mantine-color-body": colors["fond-page"],
    "--mantine-color-text": colors["texte-defaut"],
    "--mantine-color-dimmed": colors["texte-mention"],
    "--mantine-color-default-border": colors["bordure-defaut"],
    "--mantine-color-anchor": colors["texte-action"],
  },
  dark: {},
});
