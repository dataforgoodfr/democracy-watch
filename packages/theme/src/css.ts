import {
  colors,
  effects,
  fonts,
  parliamentaryGroups,
  radius,
  spacing,
  typeScale,
} from "./tokens.ts";

const px = (value: number) => `${value}px`;

/** Toutes les variables CSS `--dw-*`, dans l'ordre d'affichage. */
export const cssVariables = (): [string, string][] => [
  ...Object.entries(colors).map(([name, value]): [string, string] => [`--dw-${name}`, value]),
  ...Object.entries(parliamentaryGroups).map(([code, group]): [string, string] => [
    `--dw-groupe-${code.toLowerCase()}`,
    group.color,
  ]),
  ["--dw-police-interface", fonts.interface],
  ["--dw-police-loi", fonts.loi],
  ["--dw-police-code", fonts.code],
  ...Object.entries(typeScale).flatMap(([name, style]): [string, string][] => [
    [`--dw-texte-${name}-taille`, px(style.size)],
    [`--dw-texte-${name}-interligne`, px(style.lineHeight)],
  ]),
  ...Object.entries(spacing).map(([name, value]): [string, string] => [
    `--dw-espacement-${name}`,
    px(value),
  ]),
  ...Object.entries(radius).map(([name, value]): [string, string] => [
    `--dw-rayon-${name}`,
    px(value),
  ]),
  ...Object.entries(effects).map(([name, value]): [string, string] => [`--dw-${name}`, value]),
];

/** Contenu de `tokens.css`. */
export const tokensCss = () => {
  const lines = cssVariables().map(([name, value]) => `  ${name}: ${value};`);
  return [
    "/* Fichier généré par `pnpm --filter @democracy-watch/theme generate` depuis src/tokens.ts. Ne pas modifier. */",
    ":root {",
    ...lines,
    "}",
    "",
  ].join("\n");
};
