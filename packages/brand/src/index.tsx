import type { SVGProps } from "react";
import { hemicycleDots, irisPath, lidPath, PICTO_VIEWBOX } from "./geometry.ts";

export * from "./geometry.ts";

type PictoProps = Omit<SVGProps<SVGSVGElement>, "viewBox"> & {
  /** Couleur du pictogramme (par défaut : couleur du texte courant). */
  color?: string;
  /** Variante à deux rangées, lisible aux petites tailles. */
  compact?: boolean;
  title?: string;
};

const compactOptions = { rows: [44, 31], spacing: 11, dotRadius: 3.4 } as const;

/** Pictogramme Democracy Watch : l'hémicycle forme un œil. */
export const Picto = ({ color = "currentColor", compact = false, title, ...props }: PictoProps) => {
  const { x, y, width, height } = PICTO_VIEWBOX;
  return (
    // biome-ignore lint/a11y/noSvgWithoutTitle: titre rendu si fourni, sinon le pictogramme est décoratif (aria-hidden).
    <svg
      viewBox={`${x} ${y} ${width} ${height}`}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      {hemicycleDots(compact ? compactOptions : undefined).map((dot) => (
        <circle key={`${dot.cx}-${dot.cy}`} cx={dot.cx} cy={dot.cy} r={dot.r} fill={color} />
      ))}
      <path d={irisPath()} fill={color} fillRule="evenodd" />
      <path d={lidPath()} fill={color} />
    </svg>
  );
};

type LogoProps = {
  /** horizontal : picto + nom ; picto : pictogramme seul. */
  variant?: "horizontal" | "picto";
  /** Hauteur du pictogramme, en px. */
  size?: number;
  color?: string;
  className?: string;
};

/** Logo complet. Le nom utilise Archivo ExtraBold Italic, chargée par @democracy-watch/theme. */
export const Logo = ({
  variant = "horizontal",
  size = 36,
  color = "#17322E",
  className,
}: LogoProps) => (
  <span
    className={className}
    style={{ display: "inline-flex", alignItems: "center", gap: size * 0.28, color }}
  >
    <Picto
      height={size}
      width={(size * PICTO_VIEWBOX.width) / PICTO_VIEWBOX.height}
      color={color}
    />
    {variant === "horizontal" ? (
      <span
        style={{
          fontFamily: '"Archivo", arial, sans-serif',
          fontWeight: 800,
          fontStyle: "italic",
          fontSize: size * 0.56,
          lineHeight: 1,
          whiteSpace: "nowrap",
        }}
      >
        Democracy Watch
      </span>
    ) : (
      <span className="dw-visually-hidden">Democracy Watch</span>
    )}
  </span>
);
