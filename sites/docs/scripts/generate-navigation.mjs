/**
 * Génère zudoku.navigation.ts à partir de l'arborescence de la documentation.
 *
 *   - un dossier = une catégorie ; les dossiers de premier niveau sont les onglets du header ;
 *   - ordre : `index` d'abord, puis les fichiers, puis les dossiers, par nom (préfixes `01-`) ;
 *   - page : libellé et icône lus dans le frontmatter (`sidebar_label`, `sidebar_icon`, sinon
 *     `title`) ; URL dérivée du chemin sans les préfixes (routes.mjs), ou `slug` s'il est fourni ;
 *   - catégorie : libellé et icône lus dans `_category.json` (`label`, `icon`, `collapsible`),
 *     sinon le nom du dossier mis en forme.
 *
 * Usage : node scripts/generate-navigation.mjs          (écrit le fichier)
 *         node scripts/generate-navigation.mjs --check  (échoue si le fichier n'est pas à jour)
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { routeFromRelPath, stripOrder } from "./routes.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT = path.join(ROOT, "zudoku.navigation.ts");
const IGNORED = new Set(["node_modules", "dist", "public", "scripts", "src", ".turbo"]);
const DEFAULT_ICON = { page: "file-text", category: "folder" };

/** Frontmatter YAML simple (clé: valeur sur une ligne). */
const frontmatter = (file) => {
  const match = fs.readFileSync(file, "utf8").match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  return Object.fromEntries(
    match[1]
      .split(/\r?\n/)
      .map((line) => line.match(/^([\w-]+):\s*(.*)$/))
      .filter(Boolean)
      .map(([, key, value]) => [key, value.trim().replace(/^["']|["']$/g, "")]),
  );
};

/** `analyse-existant` → `Analyse existant` (repli quand rien n'est déclaré). */
const formatLabel = (name) => {
  const words = stripOrder(name).split(/[-_]+/).join(" ");
  return words.charAt(0).toUpperCase() + words.slice(1);
};

const isPage = (name) => /\.mdx?$/.test(name);
const isIndex = (name) => /^index\.mdx?$/.test(name);

const sortEntries = (a, b) => {
  if (isIndex(a.name) !== isIndex(b.name)) return isIndex(a.name) ? -1 : 1;
  if (a.isFile() !== b.isFile()) return a.isFile() ? -1 : 1;
  return a.name.localeCompare(b.name, "fr", { numeric: true, sensitivity: "base" });
};

const page = (absolute, relative) => {
  const meta = frontmatter(absolute);
  return {
    type: "doc",
    file: relative,
    path: meta.slug ?? routeFromRelPath(relative),
    label:
      meta.sidebar_label ??
      meta.title ??
      formatLabel(path.basename(relative).replace(/\.mdx?$/, "")),
    icon: meta.sidebar_icon ?? DEFAULT_ICON.page,
  };
};

const category = (absolute, name, items) => {
  const configFile = path.join(absolute, "_category.json");
  const config = fs.existsSync(configFile) ? JSON.parse(fs.readFileSync(configFile, "utf8")) : {};
  return {
    type: "category",
    label: config.label ?? formatLabel(name),
    icon: config.icon ?? DEFAULT_ICON.category,
    ...(config.collapsible === false ? { collapsible: false } : {}),
    items,
  };
};

const scan = (directory, depth = 0) =>
  fs
    .readdirSync(directory, { withFileTypes: true })
    .filter((entry) => !entry.name.startsWith(".") && !entry.name.startsWith("_"))
    .filter((entry) => !(depth === 0 && IGNORED.has(entry.name)))
    .filter((entry) => entry.isDirectory() || isPage(entry.name))
    // Les pages à la racine (hors rubrique) ne sont pas prévues : tout vit dans une rubrique.
    .filter((entry) => depth > 0 || entry.isDirectory())
    .sort(sortEntries)
    .flatMap((entry) => {
      const absolute = path.join(directory, entry.name);
      const relative = path.relative(ROOT, absolute).replace(/\\/g, "/");
      if (entry.isFile()) return [page(absolute, relative)];
      const items = scan(absolute, depth + 1);
      return items.length > 0 ? [category(absolute, entry.name, items)] : [];
    });

const render = (
  items,
) => `// Fichier généré par scripts/generate-navigation.mjs depuis l'arborescence. Ne pas modifier.
import type { ZudokuConfig } from "zudoku";

export const navigation: ZudokuConfig["navigation"] = ${JSON.stringify(items, null, 2)};
`;

/** Mise en forme du dépôt (Biome), pour que le fichier généré passe `pnpm check`. */
const format = (content) => {
  try {
    return execFileSync("pnpm", ["exec", "biome", "format", "--stdin-file-path", OUTPUT], {
      cwd: ROOT,
      input: content,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "ignore"],
    });
  } catch {
    return content;
  }
};

const content = format(render(scan(ROOT)));

if (process.argv.includes("--check")) {
  const current = fs.existsSync(OUTPUT) ? fs.readFileSync(OUTPUT, "utf8") : "";
  if (current !== content) {
    console.error(
      "✗ zudoku.navigation.ts n'est pas à jour : pnpm --filter @democracy-watch/docs docs:nav",
    );
    process.exit(1);
  }
  console.log("✓ navigation à jour");
} else {
  fs.writeFileSync(OUTPUT, content);
  console.log(`✓ ${path.relative(process.cwd(), OUTPUT)}`);
}
