import { defineConfig } from "vite";

/**
 * Dépendances publiées en CommonJS (rendu MDX et diagrammes) : Vite doit les pré-bundler en
 * développement, sinon le navigateur échoue sur « does not provide an export named 'default' ».
 * `style-to-js` et `style-to-object` sont déclarées dans package.json pour être résolubles
 * malgré l'isolation de pnpm. Même réglage que CLAIR.
 */
const COMMONJS_DEPENDENCIES = ["mermaid", "style-to-js", "style-to-object"];

/**
 * Modules virtuels fournis par Zudoku : l'analyse des dépendances de Vite ne peut pas les
 * résoudre ; sans cette exclusion, elle échoue et désactive tout le pré-bundling.
 */
const ZUDOKU_VIRTUAL_MODULES = [
  "virtual:zudoku-api-keys-plugin",
  "virtual:zudoku-api-plugins",
  "virtual:zudoku-auth",
  "virtual:zudoku-config",
  "virtual:zudoku-custom-pages-plugin",
  "virtual:zudoku-docs-plugin",
  "virtual:zudoku-markdown-files",
  "virtual:zudoku-navigation",
  "virtual:zudoku-search-plugin",
  "virtual:zudoku-shiki-register",
  "virtual:zudoku-theme.css",
];

export default defineConfig({
  server: {
    watch: { ignored: ["**/dist/**"] },
  },
  ssr: { noExternal: COMMONJS_DEPENDENCIES },
  optimizeDeps: {
    include: COMMONJS_DEPENDENCIES,
    exclude: ZUDOKU_VIRTUAL_MODULES,
  },
});
