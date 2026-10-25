// Adresse publique d'une page, à partir de son chemin dans sites/docs.
//
// Les préfixes numériques des dossiers (`01-accueil`, `03-front`) ne servent qu'à ordonner la
// navigation : ils n'apparaissent pas dans les URLs, pour que réordonner une rubrique ne casse
// aucun lien. La navigation et les tests partagent cette fonction pour ne jamais diverger.

/** Retire les préfixes d'ordre (`01-`, `01-02-`) d'un nom de dossier ou de fichier. */
export const stripOrder = (name) => name.replace(/^(\d+-)+/, "");

/** `03-front/01-architecture/pages.mdx` → `/front/architecture/pages` ; `…/index.mdx` → le dossier. */
export const routeFromRelPath = (relPath) => {
  const segments = relPath
    .replace(/\\/g, "/")
    .replace(/\.mdx?$/, "")
    .split("/")
    .map(stripOrder)
    .filter((segment, index, all) => !(segment === "index" && index === all.length - 1));
  return `/${segments.join("/")}`;
};
