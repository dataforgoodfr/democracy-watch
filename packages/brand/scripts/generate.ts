/**
 * Génère les assets de marque depuis la géométrie du pictogramme et la police Archivo :
 *   - assets/*.svg : pictogramme, logotypes (texte vectorisé), favicon
 *   - assets/*.png, favicon.ico, site.webmanifest, og-image.png
 *   - proposition-logo.png : planche de propositions autour du thème hémicycle-œil
 * Puis copie les fichiers servis par les sites dans sites/web/public et sites/docs/public.
 *
 * Usage : pnpm brand
 */
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import opentype from "opentype.js";
import sharp from "sharp";
import { hemicycleDots, irisPath, lidPath, PICTO_VIEWBOX, pictoMarkup } from "../src/geometry.ts";

const require = createRequire(import.meta.url);
const root = new URL("../", import.meta.url);
const assets = new URL("assets/", root);
const sites = ["../../sites/web/public/", "../../sites/docs/public/"].map(
  (path) => new URL(path, root),
);

const C = {
  vert: "#17322E",
  jaune: "#F5FAC4",
  jauneVif: "#EDF58A",
  jaunePale: "#F7FBDD",
  sarcelle: "#2E9F92",
  sarcelleTexte: "#1F6F66",
  sarcellePale: "#E3F4F1",
  page: "#F6F6F6",
  mention: "#666666",
  blanc: "#FFFFFF",
};

const loadFont = (file: string) => {
  const buffer = readFileSync(require.resolve(`@fontsource/archivo/files/${file}`));
  return opentype.parse(
    buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength),
  );
};
const logoFont = loadFont("archivo-latin-800-italic.woff");
const labelFont = loadFont("archivo-latin-700-normal.woff");
const textFont = loadFont("archivo-latin-400-normal.woff");

/**
 * Texte vectorisé glyphe par glyphe (avec crénage) : pas de dépendance à une police installée.
 * On évite `font.getPath`, qui échoue sur certaines tables de substitution d'Archivo.
 */

/** Crénage entre deux glyphes ; opentype.js renvoie parfois une valeur non numérique. */
const kerning = (font: opentype.Font, left: opentype.Glyph, right?: opentype.Glyph) => {
  const value = right ? font.getKerningValue(left, right) : 0;
  return Number.isFinite(value) ? value : 0;
};

const glyphRun = (font: opentype.Font, text: string, size: number) => {
  const scale = size / font.unitsPerEm;
  const glyphs = [...text].map((char) => font.charToGlyph(char));
  let x = 0;
  return glyphs.map((glyph, index) => {
    const position = x;
    const next = glyphs[index + 1];
    x += (glyph.advanceWidth ?? 0) * scale + kerning(font, glyph, next) * scale;
    return { glyph, x: position, end: x };
  });
};

/**
 * Tracé SVG d'un glyphe depuis ses contours bruts (unités de la police). opentype.js produit
 * parfois un point de contrôle invalide : la courbe devient alors un segment droit.
 */
const glyphPathData = (glyph: opentype.Glyph, x: number, y: number, scale: number) => {
  const px = (value: number | undefined) => (x + (value ?? 0) * scale).toFixed(2);
  const py = (value: number | undefined) => (y - (value ?? 0) * scale).toFixed(2);
  const ok = (...values: (number | undefined)[]) => values.every((value) => Number.isFinite(value));
  return glyph.path.commands
    .map((command) => {
      switch (command.type) {
        case "M":
        case "L":
          return `${command.type}${px(command.x)} ${py(command.y)}`;
        case "Q":
          return ok(command.x1, command.y1)
            ? `Q${px(command.x1)} ${py(command.y1)} ${px(command.x)} ${py(command.y)}`
            : `L${px(command.x)} ${py(command.y)}`;
        case "C":
          return ok(command.x1, command.y1, command.x2, command.y2)
            ? `C${px(command.x1)} ${py(command.y1)} ${px(command.x2)} ${py(command.y2)} ${px(command.x)} ${py(command.y)}`
            : `L${px(command.x)} ${py(command.y)}`;
        default:
          return "Z";
      }
    })
    .join("");
};

const textPath = (
  font: opentype.Font,
  text: string,
  x: number,
  y: number,
  size: number,
  fill: string,
) =>
  `<path d="${glyphRun(font, text, size)
    .map(({ glyph, x: offset }) => glyphPathData(glyph, x + offset, y, size / font.unitsPerEm))
    .join(" ")}" fill="${fill}"/>`;

const textWidth = (font: opentype.Font, text: string, size: number) =>
  glyphRun(font, text, size).at(-1)?.end ?? 0;

const NAME = "Democracy Watch";
const { width: PW, height: PH } = PICTO_VIEWBOX;

/** Pictogramme placé en (x, y) avec une hauteur donnée. */
const placePicto = (inner: string, x: number, y: number, height: number) =>
  `<g transform="translate(${x} ${y}) scale(${height / PH})">${inner}</g>`;

const svg = (width: number, height: number, body: string, background?: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${
    background ? `<rect width="${width}" height="${height}" fill="${background}"/>` : ""
  }${body}</svg>`;

// ─── Logotypes ──────────────────────────────────────────────────────────────

const horizontalLogo = (ink: string, text = ink) => {
  const height = 56;
  const pictoWidth = (PW * height) / PH;
  const size = 30;
  const gap = 14;
  const width = Math.ceil(pictoWidth + gap + textWidth(logoFont, NAME, size) + 4);
  return svg(
    width,
    height,
    placePicto(pictoMarkup({ ink }), 0, 0, height) +
      textPath(logoFont, NAME, pictoWidth + gap, 39, size, text),
  );
};

const stackedLogo = (ink: string) => {
  const size = 30;
  const width = Math.ceil(textWidth(logoFont, NAME, size) + 8);
  const pictoHeight = 84;
  const pictoWidth = (PW * pictoHeight) / PH;
  return svg(
    width,
    pictoHeight + 48,
    placePicto(pictoMarkup({ ink }), (width - pictoWidth) / 2, 0, pictoHeight) +
      textPath(logoFont, NAME, 4, pictoHeight + 38, size, ink),
  );
};

/** Variante lisible en 16–48 px : moins de rangées, sièges plus gros. */
const compactOptions = { rows: [44, 31], spacing: 11, dotRadius: 3.4 } as const;

const tile = (
  size: number,
  background: string,
  ink: string,
  radius = size * 0.22,
  options = compactOptions,
) => {
  const height = size * 0.56;
  const width = (PW * height) / PH;
  return svg(
    size,
    size,
    `<rect width="${size}" height="${size}" rx="${radius}" fill="${background}"/>` +
      placePicto(
        pictoMarkup({ ink }, options),
        (size - width) / 2,
        (size - height) / 2 + size * 0.03,
        height,
      ),
  );
};

// ─── Favicon .ico (entrées PNG) ─────────────────────────────────────────────

const ico = (pngs: { size: number; data: Buffer }[]) => {
  const header = Buffer.alloc(6 + 16 * pngs.length);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(pngs.length, 4);
  let offset = header.length;
  pngs.forEach(({ size, data }, index) => {
    const entry = 6 + 16 * index;
    header.writeUInt8(size >= 256 ? 0 : size, entry);
    header.writeUInt8(size >= 256 ? 0 : size, entry + 1);
    header.writeUInt16LE(1, entry + 4);
    header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(data.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += data.length;
  });
  return Buffer.concat([header, ...pngs.map(({ data }) => data)]);
};

const png = (source: string, width: number, height = width) =>
  sharp(Buffer.from(source), { density: 300 }).resize(width, height).png().toBuffer();

// ─── Image Open Graph ───────────────────────────────────────────────────────

const ogImage = () => {
  const W = 1200;
  const H = 630;
  const pictoHeight = 230;
  return svg(
    W,
    H,
    `<rect x="40" y="40" width="${W - 80}" height="${H - 80}" rx="28" fill="${C.jaune}"/>` +
      placePicto(pictoMarkup({ ink: C.vert }), 110, 120, pictoHeight) +
      textPath(logoFont, NAME, 110, 450, 84, C.vert) +
      textPath(textFont, "Veille législative pour les associations et ONG", 112, 515, 34, C.vert),
    C.page,
  );
};

// ─── Planche de propositions ────────────────────────────────────────────────

const GROUP_COLORS = [
  "#E91D27",
  "#A50F1F",
  "#E2457A",
  "#2E9E4F",
  "#C49A00",
  "#F08A24",
  "#8C5CC4",
  "#2F7FC1",
  "#2340B8",
  "#1D2B6B",
];

/** Sièges colorés de gauche à droite, comme la composition d'un hémicycle. */
const parliamentPicto = (ink: string) => {
  const dots = hemicycleDots()
    .map((dot) => {
      const angle = Math.atan2(48 - dot.cy, 50 - dot.cx); // 0 à gauche → π à droite
      const index = Math.min(
        GROUP_COLORS.length - 1,
        Math.floor((angle / Math.PI) * GROUP_COLORS.length),
      );
      return `<circle cx="${dot.cx}" cy="${dot.cy}" r="${dot.r}" fill="${GROUP_COLORS[index]}"/>`;
    })
    .join("");
  return `${dots}<path d="${irisPath()}" fill="${ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${ink}"/>`;
};

/** Arcs continus à la place des sièges. */
const monolinePicto = (ink: string) =>
  [44, 37, 30, 23]
    .map((r, row) => {
      const start = row === 0 ? 0.16 : 0;
      const [x1, y1] = [50 - r * Math.cos(start), 48 - r * Math.sin(start)];
      const [x2, y2] = [50 + r * Math.cos(start), 48 - r * Math.sin(start)];
      return `<path d="M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}" fill="none" stroke="${ink}" stroke-width="3" stroke-linecap="round" stroke-dasharray="${row % 2 ? "0.1 6.6" : "none"}"/>`;
    })
    .join("") +
  `<path d="${irisPath()}" fill="${ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${ink}"/>`;

/** Quelques sièges « surveillés » mis en avant. */
const watchedPicto = (ink: string, accent: string) => {
  const dots = hemicycleDots()
    .map((dot, index) => {
      const lit = [5, 9, 26, 31, 47].includes(index);
      return `<circle cx="${dot.cx}" cy="${dot.cy}" r="${lit ? dot.r * 1.5 : dot.r}" fill="${lit ? accent : ink}"/>`;
    })
    .join("");
  return `${dots}<path d="${irisPath()}" fill="${ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${ink}"/>`;
};

/** Sièges en anneaux (contour). */
const outlinePicto = (ink: string) =>
  hemicycleDots()
    .map(
      (dot) =>
        `<circle cx="${dot.cx}" cy="${dot.cy}" r="${dot.r * 0.85}" fill="none" stroke="${ink}" stroke-width="0.9"/>`,
    )
    .join("") +
  `<path d="${irisPath()}" fill="${ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${ink}"/>`;

/** Sièges carrés. */
const squarePicto = (ink: string) =>
  hemicycleDots()
    .map((dot) => {
      const angle = (Math.atan2(48 - dot.cy, 50 - dot.cx) * 180) / Math.PI;
      const s = dot.r * 1.8;
      return `<rect x="${dot.cx - s / 2}" y="${dot.cy - s / 2}" width="${s}" height="${s}" rx="0.4" transform="rotate(${angle} ${dot.cx} ${dot.cy})" fill="${ink}"/>`;
    })
    .join("") +
  `<path d="${irisPath()}" fill="${ink}" fill-rule="evenodd"/><path d="${lidPath()}" fill="${ink}"/>`;

/** Œil en amande : une paupière supérieure ferme l'hémicycle. */
const almondPicto = (ink: string) =>
  `${pictoMarkup({ ink }, { rows: [37, 30, 23] })}<path d="M 5 47.5 Q 50 -14 95 47.5" fill="none" stroke="${ink}" stroke-width="3" stroke-linecap="round"/>`;

type Proposal = {
  title: string;
  note: string;
  background: string;
  render: (cardWidth: number) => string;
};

const centered = (inner: string, cardWidth: number, height = 150) => {
  const width = (PW * height) / PH;
  return placePicto(inner, (cardWidth - width) / 2, 46, height);
};

const proposals: Proposal[] = [
  {
    title: "A · Référence",
    note: "Styleguide V1 : vert encre sur jaune clair",
    background: C.jaune,
    render: (w) => centered(pictoMarkup({ ink: C.vert }), w),
  },
  {
    title: "B · Inversé",
    note: "Jaune clair sur vert encre",
    background: C.vert,
    render: (w) => centered(pictoMarkup({ ink: C.jaune }), w),
  },
  {
    title: "C · Hémicycle des groupes",
    note: "Sièges aux couleurs des groupes",
    background: C.blanc,
    render: (w) => centered(parliamentPicto(C.vert), w),
  },
  {
    title: "D · Iris sarcelle",
    note: "Accent sarcelle sur l'iris",
    background: C.jaunePale,
    render: (w) => centered(pictoMarkup({ ink: C.vert, iris: C.sarcelle }), w),
  },
  {
    title: "E · Rangées en dégradé",
    note: "Du vert encre à la sarcelle",
    background: C.blanc,
    render: (w) =>
      centered(
        pictoMarkup({ ink: C.vert, rowColors: [C.vert, C.sarcelleTexte, C.sarcelle, "#7CC9BE"] }),
        w,
      ),
  },
  {
    title: "F · Sièges surveillés",
    note: "Quelques sièges en jaune vif",
    background: C.vert,
    render: (w) => centered(watchedPicto(C.jaune, C.jauneVif), w),
  },
  {
    title: "G · Monoline",
    note: "Arcs continus et pointillés",
    background: C.jaune,
    render: (w) => centered(monolinePicto(C.vert), w),
  },
  {
    title: "H · Sièges en contour",
    note: "Plus léger, pour les grands formats",
    background: C.blanc,
    render: (w) => centered(outlinePicto(C.vert), w),
  },
  {
    title: "I · Sièges carrés",
    note: "Évoque les pupitres de l'hémicycle",
    background: C.jaunePale,
    render: (w) => centered(squarePicto(C.vert), w),
  },
  {
    title: "J · Œil en amande",
    note: "Paupière supérieure fermant l'arc",
    background: C.jaune,
    render: (w) => centered(almondPicto(C.vert), w),
  },
  {
    title: "K · Compact (favicon)",
    note: "2 rangées, lisible en 16 px",
    background: C.blanc,
    render: (w) => centered(pictoMarkup({ ink: C.vert }, compactOptions), w),
  },
  {
    title: "L · Monochrome",
    note: "Impression, tampon, noir pur",
    background: C.blanc,
    render: (w) => centered(pictoMarkup({ ink: "#161616" }), w),
  },
  {
    title: "M · Tuile d'application",
    note: "Icône mobile et réseaux sociaux",
    background: C.page,
    render: (w) =>
      `<g transform="translate(${(w - 170) / 2} 36)">${tile(170, C.vert, C.jaune).replace(/^<svg[^>]*>|<\/svg>$/g, "")}</g>`,
  },
  {
    title: "N · Pastille ronde",
    note: "Avatar, badge, réseaux",
    background: C.page,
    render: (w) =>
      `<circle cx="${w / 2}" cy="121" r="88" fill="${C.jaune}"/>` +
      placePicto(pictoMarkup({ ink: C.vert }), w / 2 - 63, 82, 88),
  },
  {
    title: "O · Logotype horizontal",
    note: "Picto + Archivo ExtraBold Italic",
    background: C.jaune,
    render: (w) => {
      const size = 26;
      const height = 52;
      const pw = (PW * height) / PH;
      const total = pw + 10 + textWidth(logoFont, NAME, size);
      const x = (w - total) / 2;
      return (
        placePicto(pictoMarkup({ ink: C.vert }), x, 96, height) +
        textPath(logoFont, NAME, x + pw + 10, 133, size, C.vert)
      );
    },
  },
  {
    title: "P · Logotype empilé",
    note: "Pour les formats carrés",
    background: C.blanc,
    render: (w) => {
      const size = 28;
      return (
        placePicto(pictoMarkup({ ink: C.vert }), (w - (PW * 100) / PH) / 2, 40, 100) +
        textPath(logoFont, NAME, (w - textWidth(logoFont, NAME, size)) / 2, 182, size, C.vert)
      );
    },
  },
];

const board = () => {
  const columns = 4;
  const cardW = 360;
  const cardH = 300;
  const gap = 24;
  const margin = 56;
  const headerH = 150;
  const rows = Math.ceil(proposals.length / columns);
  const W = margin * 2 + columns * cardW + (columns - 1) * gap;
  const H = headerH + margin + rows * cardH + (rows - 1) * gap;
  const cards = proposals
    .map((proposal, index) => {
      const x = margin + (index % columns) * (cardW + gap);
      const y = headerH + Math.floor(index / columns) * (cardH + gap);
      const dark = proposal.background === C.vert;
      return `<g transform="translate(${x} ${y})">
        <rect width="${cardW}" height="${cardH}" rx="16" fill="${C.blanc}" stroke="#DDDDDD"/>
        <clipPath id="clip${index}"><rect width="${cardW}" height="232" rx="16"/></clipPath>
        <g clip-path="url(#clip${index})"><rect width="${cardW}" height="232" fill="${proposal.background}"/>${proposal.render(cardW)}</g>
        <line x1="0" y1="232" x2="${cardW}" y2="232" stroke="#DDDDDD"/>
        ${textPath(labelFont, proposal.title, 20, 262, 18, dark ? C.vert : C.vert)}
        ${textPath(textFont, proposal.note, 20, 286, 14, C.mention)}
      </g>`;
    })
    .join("");
  return svg(
    W,
    H,
    textPath(logoFont, "Democracy Watch — propositions de logo", margin, 84, 40, C.vert) +
      textPath(
        textFont,
        "Thème : l'hémicycle forme un œil qui veille. Variantes de couleur, de forme et de format.",
        margin,
        118,
        18,
        C.mention,
      ) +
      cards,
    C.page,
  );
};

// ─── Écriture ───────────────────────────────────────────────────────────────

const write = async (name: string, content: string | Buffer | Promise<Buffer>) => {
  writeFileSync(new URL(name, assets), await content);
  console.log(`✓ assets/${name}`);
};

mkdirSync(assets, { recursive: true });

const faviconSvg = tile(64, C.jaune, C.vert, 14);

await write("picto.svg", svg(PW, PH, pictoMarkup({ ink: C.vert })));
await write("picto-inverse.svg", svg(PW, PH, pictoMarkup({ ink: C.jaune })));
await write("logo.svg", horizontalLogo(C.vert));
await write("logo-inverse.svg", horizontalLogo(C.jaune));
await write("logo-stacked.svg", stackedLogo(C.vert));
await write("favicon.svg", faviconSvg);
await write(
  "favicon.ico",
  ico(
    await Promise.all(
      [16, 32, 48].map(async (size) => ({
        size,
        data: await png(tile(size, C.jaune, C.vert, size * 0.22), size),
      })),
    ),
  ),
);
await write("apple-touch-icon.png", png(tile(180, C.jaune, C.vert, 0), 180));
await write("icon-192.png", png(tile(192, C.jaune, C.vert), 192));
await write("icon-512.png", png(tile(512, C.jaune, C.vert), 512));
await write("icon-maskable-512.png", png(tile(512, C.jaune, C.vert, 0, compactOptions), 512));
await write("og-image.png", png(ogImage(), 1200, 630));
await write(
  "site.webmanifest",
  `${JSON.stringify(
    {
      name: NAME,
      short_name: NAME,
      icons: [
        { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
        { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
        { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
      ],
      theme_color: C.vert,
      background_color: C.jaune,
      display: "standalone",
    },
    null,
    2,
  )}\n`,
);

const boardSvg = board();
writeFileSync(
  new URL("proposition-logo.png", root),
  await sharp(Buffer.from(boardSvg), { density: 144 }).png().toBuffer(),
);
console.log("✓ proposition-logo.png");
// La planche est aussi publiée dans la documentation (page « Logo et favicons »).
copyFileSync(
  new URL("proposition-logo.png", root),
  new URL("../../sites/docs/public/proposition-logo.png", root),
);

const served = [
  "favicon.svg",
  "favicon.ico",
  "apple-touch-icon.png",
  "icon-192.png",
  "icon-512.png",
  "icon-maskable-512.png",
  "og-image.png",
  "site.webmanifest",
  "logo.svg",
  "logo-inverse.svg",
];
for (const site of sites) {
  mkdirSync(site, { recursive: true });
  for (const file of served) copyFileSync(new URL(file, assets), new URL(file, site));
  console.log(`✓ copié dans ${site.pathname}`);
}
