/**
 * Géométrie du pictogramme Democracy Watch : un hémicycle de sièges (points) qui forme un œil.
 * Source unique, utilisée par le composant React et par le générateur d'assets
 * (favicons, image OG, planche de propositions).
 *
 * Repère : viewBox de 100 × 70, centre de l'iris en (50, 48).
 */

export const PICTO_VIEWBOX = { x: 0, y: 0, width: 100, height: 70 } as const;

const CENTER = { x: 50, y: 48 };

export type Dot = { cx: number; cy: number; r: number; row: number };

export type PictoOptions = {
  /** Rayons des rangées de sièges, de l'extérieur vers l'intérieur. */
  rows?: readonly number[];
  /** Écart visé entre deux sièges, le long de l'arc. */
  spacing?: number;
  /** Rayon d'un siège. */
  dotRadius?: number;
};

const DEFAULT_ROWS = [44, 37, 30, 23] as const;

const round = (value: number) => Math.round(value * 100) / 100;

/** Sièges de l'hémicycle. La rangée extérieure s'arrête un peu au-dessus de la paupière. */
export const hemicycleDots = ({
  rows = DEFAULT_ROWS,
  spacing = 6.6,
  dotRadius = 1.7,
}: PictoOptions = {}): Dot[] =>
  rows.flatMap((radius, row) => {
    const startAngle = row === 0 ? (9 * Math.PI) / 180 : 0;
    const sweep = Math.PI - 2 * startAngle;
    const count = Math.max(2, Math.round((radius * sweep) / spacing) + 1);
    return Array.from({ length: count }, (_, index) => {
      const angle = startAngle + (sweep * index) / (count - 1);
      return {
        cx: round(CENTER.x - radius * Math.cos(angle)),
        cy: round(CENTER.y - radius * Math.sin(angle)),
        r: dotRadius,
        row,
      };
    });
  });

/** Iris : un anneau (tracé pair-impair). */
export const irisPath = (outer = 14, inner = 5.6) => {
  const ring = (r: number) =>
    `M ${CENTER.x - r} ${CENTER.y} a ${r} ${r} 0 1 0 ${2 * r} 0 a ${r} ${r} 0 1 0 ${-2 * r} 0 Z`;
  return `${ring(outer)} ${ring(inner)}`;
};

/** Paupière inférieure : une courbe, plus épaisse au centre. */
export const lidPath = () => {
  const left = { x: 5, y: CENTER.y - 0.5 };
  const right = { x: 95, y: CENTER.y - 0.5 };
  // Deux courbes (haut et bas) donnent une forme fuselée, aux bouts arrondis.
  return [
    `M ${left.x} ${left.y}`,
    `Q ${CENTER.x} ${CENTER.y + 30} ${right.x} ${right.y}`,
    `a 1.6 1.6 0 0 1 0.4 2.6`,
    `Q ${CENTER.x} ${CENTER.y + 36} ${left.x - 0.4} ${left.y + 2.6}`,
    `a 1.6 1.6 0 0 1 0.4 -2.6 Z`,
  ].join(" ");
};

export type PictoColors = {
  ink: string;
  dots?: string;
  iris?: string;
  rowColors?: readonly string[];
};

/** Contenu SVG (sans balise <svg>) du pictogramme. */
export const pictoMarkup = (colors: PictoColors, options?: PictoOptions) => {
  const dots = hemicycleDots(options)
    .map((dot) => {
      const fill = colors.rowColors?.[dot.row] ?? colors.dots ?? colors.ink;
      return `<circle cx="${dot.cx}" cy="${dot.cy}" r="${dot.r}" fill="${fill}"/>`;
    })
    .join("");
  return `${dots}<path d="${irisPath()}" fill="${colors.iris ?? colors.ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${colors.ink}"/>`;
};

export const pictoSvg = (colors: PictoColors, options?: PictoOptions) => {
  const { x, y, width, height } = PICTO_VIEWBOX;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${x} ${y} ${width} ${height}" role="img" aria-label="Democracy Watch">${pictoMarkup(colors, options)}</svg>`;
};
