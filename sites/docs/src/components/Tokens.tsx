import {
  colors,
  effects,
  palette,
  parliamentaryGroups,
  radius,
  spacing,
  standardization,
  typeScale,
} from "@democracy-watch/theme";

const Swatch = ({ name, value, note }: { name: string; value: string; note?: string }) => (
  <div className="dw-swatch">
    <div style={{ background: value }} />
    <div>
      <strong>{name}</strong>
      <br />
      <code>{value}</code>
      {note ? (
        <>
          <br />
          <small>{note}</small>
        </>
      ) : null}
    </div>
  </div>
);

/** Nuancier lu directement dans packages/theme/src/tokens.ts. */
export const ColorSwatches = ({ set }: { set: "palette" | "semantique" | "groupes" }) => (
  <div className="dw-swatches">
    {set === "palette" &&
      Object.entries(palette).map(([name, value]) => (
        <Swatch key={name} name={name} value={value} />
      ))}
    {set === "semantique" &&
      Object.entries(colors).map(([name, value]) => (
        <Swatch key={name} name={`--dw-${name}`} value={value} />
      ))}
    {set === "groupes" &&
      Object.entries(parliamentaryGroups).map(([code, group]) => (
        <Swatch
          key={code}
          name={`${code} · --dw-groupe-${code.toLowerCase()}`}
          value={group.color}
          note={`${group.label} (${group.source})`}
        />
      ))}
  </div>
);

export const TypeScale = () => (
  <table>
    <thead>
      <tr>
        <th>Style</th>
        <th>Aperçu</th>
        <th>Taille / interligne</th>
        <th>Mobile</th>
        <th>Graisse</th>
      </tr>
    </thead>
    <tbody>
      {Object.entries(typeScale).map(([name, style]) => (
        <tr key={name}>
          <td>
            <code>{name}</code>
          </td>
          <td
            style={{
              fontSize: Math.min(style.size, 28),
              fontWeight: style.weight,
              fontStyle: "italic" in style ? "italic" : undefined,
              fontFamily:
                "family" in style && style.family === "loi"
                  ? "Spectral, serif"
                  : "Archivo, sans-serif",
              textTransform: "uppercase" in style ? "uppercase" : undefined,
            }}
          >
            {name === "logo" ? "Democracy Watch" : "Projet de loi agricole"}
          </td>
          <td>
            {style.size} / {style.lineHeight}
          </td>
          <td>{"mobile" in style ? `${style.mobile.size} / ${style.mobile.lineHeight}` : "—"}</td>
          <td>{style.weight}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

export const SpacingScale = () => (
  <table>
    <thead>
      <tr>
        <th>Token</th>
        <th>Valeur</th>
        <th>Aperçu</th>
      </tr>
    </thead>
    <tbody>
      {Object.entries(spacing).map(([name, value]) => (
        <tr key={name}>
          <td>
            <code>--dw-espacement-{name}</code>
          </td>
          <td>{value} px</td>
          <td>
            <span
              style={{
                display: "inline-block",
                width: value,
                height: 12,
                background: colors["fond-action"],
              }}
            />
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

export const RadiusScale = () => (
  <>
    <div className="dw-swatches">
      {Object.entries(radius).map(([name, value]) => (
        <div key={name} className="dw-swatch">
          <div
            style={{
              margin: 12,
              height: 48,
              background: colors["fond-marque"],
              border: `1.5px solid ${colors["bordure-action"]}`,
              borderRadius: Math.min(value, 24),
            }}
          />
          <div>
            <code>--dw-rayon-{name}</code> · {value} px
          </div>
        </div>
      ))}
    </div>
    <table>
      <tbody>
        {Object.entries(effects).map(([name, value]) => (
          <tr key={name}>
            <td>
              <code>--dw-{name}</code>
            </td>
            <td>
              <code>{value}</code>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </>
);

/** Écarts maquettes ↔ styleguide et règle retenue (source : tokens.ts). */
export const StandardizationTable = () => (
  <table>
    <thead>
      <tr>
        <th>Sujet</th>
        <th>Dans les maquettes</th>
        <th>Règle retenue (code et doc)</th>
      </tr>
    </thead>
    <tbody>
      {standardization.map((row) => (
        <tr key={row.sujet}>
          <td>{row.sujet}</td>
          <td>{row.maquette}</td>
          <td>{row.regle}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

/** Grille de captures (maquettes ou écrans réels). */
export const Captures = ({ items }: { items: { src: string; caption: string }[] }) => (
  <div className="dw-captures">
    {items.map((item) => (
      <figure key={item.src}>
        <a href={item.src}>
          <img src={item.src} alt={item.caption} loading="lazy" />
        </a>
        <figcaption>{item.caption}</figcaption>
      </figure>
    ))}
  </div>
);
