/**
 * Génère src/roadmap/issues.generated.json à partir des fiches de tickets (`*.md`) de
 * 06-roadmap/04-issues/<épique>/, 06-roadmap/05-analytics/ et 06-roadmap/06-observability/. Les fiches sont la source de vérité ; le JSON alimente
 * les Kanban, la liste des issues et l'avancement des épiques.
 *
 * Usage : node scripts/generate-roadmap.mjs          (écrit le fichier)
 *         node scripts/generate-roadmap.mjs --check  (échoue s'il n'est pas à jour)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { routeFromRelPath } from "./routes.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TICKET_DIRS = [
  "06-roadmap/04-issues",
  "06-roadmap/05-analytics",
  "06-roadmap/06-observability",
];
const OUTPUT = path.join(ROOT, "src", "roadmap", "issues.generated.json");
const STATUSES = [
  "Backlog",
  "Not Started",
  "To Implement",
  "In Progress",
  "In Testing",
  "In Review",
  "Done",
];

/** Frontmatter des fiches : chaînes entre guillemets, booléens, nombres, tableaux JSON. */
const frontmatter = (file) => {
  const block = fs.readFileSync(file, "utf8").match(/^---\r?\n([\s\S]*?)\r?\n---/)?.[1] ?? "";
  return Object.fromEntries(
    block
      .split(/\r?\n/)
      .map((line) => line.match(/^([\w-]+):\s*(.*)$/))
      .filter(Boolean)
      .map(([, key, raw]) => {
        const value = raw.trim();
        if (value.startsWith("[") || value.startsWith('"')) return [key, JSON.parse(value)];
        if (value === "true" || value === "false") return [key, value === "true"];
        if (/^\d+$/.test(value)) return [key, Number(value)];
        return [key, value];
      }),
  );
};

const order = (id) => (id.startsWith("#") ? 1000 + Number(id.slice(1)) : Number(id.slice(3)));

const issues = TICKET_DIRS.flatMap((dir) =>
  fs
    .readdirSync(path.join(ROOT, dir), { recursive: true, encoding: "utf8" })
    .filter((file) => file.endsWith(".md"))
    .map((file) => path.posix.join(dir, file.replace(/\\/g, "/"))),
)
  .map((relative) => {
    const meta = frontmatter(path.join(ROOT, relative));
    if (!STATUSES.includes(meta.status))
      throw new Error(`${relative} : statut inconnu « ${meta.status} »`);
    return {
      id: String(meta.id),
      // Le titre de page est « ID — titre » : on garde le titre seul.
      title: String(meta.title).replace(/^.+? — /, ""),
      epic: meta.epic,
      status: meta.status,
      ...(meta.size ? { size: meta.size } : {}),
      ...(meta.v0 ? { v0: true } : {}),
      ...(meta.github ? { github: meta.github } : {}),
      ...(meta.depends_on ? { dependsOn: meta.depends_on } : {}),
      ...(meta.note ? { note: meta.note } : {}),
      path: routeFromRelPath(relative),
    };
  })
  .sort((a, b) => order(a.id) - order(b.id));

const ids = new Set(issues.map((issue) => issue.id));
for (const issue of issues) {
  for (const dependency of issue.dependsOn ?? []) {
    if (!ids.has(dependency))
      throw new Error(`${issue.id} dépend de ${dependency}, qui n'a pas de fiche`);
  }
}

const content = `${JSON.stringify(issues, null, 2)}\n`;

if (process.argv.includes("--check")) {
  const current = fs.existsSync(OUTPUT) ? fs.readFileSync(OUTPUT, "utf8") : "";
  if (current !== content) {
    console.error(
      "✗ issues.generated.json n'est pas à jour : pnpm --filter @democracy-watch/docs docs:nav",
    );
    process.exit(1);
  }
  console.log("✓ roadmap à jour");
} else {
  fs.writeFileSync(OUTPUT, content);
  console.log(`✓ ${path.relative(process.cwd(), OUTPUT)} (${issues.length} tickets)`);
}
