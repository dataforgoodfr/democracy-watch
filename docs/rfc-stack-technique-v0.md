# RFC Stack technique v0

| Couche | Choix | Pourquoi ? |
|--------|-------|------------|
| **Backend** | API Rest FastAPI, sqlAlchemy, docker déployée sur Cloudify | Tout le monde connait |
| **Frontend** | vue.js dans docker deployé sur Cloudify | connue et facile à tester en local |
| **Recherche** | Meilisearch sur Cloudify (déjà en place) | pour les recherches sémentiques, mais si pas besoin on dégage |
| **BDD** | postgre de D4G | parce que<br>faut-il faire une MAJ ? |
| **Sync** | CLAIR → PG<br>PG → Meili<br>Script dans Github actions |            |
| **CI/CD** | GitHub Actions : `ruff` + `pytest` sur chaque PR, puis sur `main` build de l’image,  push sur Cloudify ?<br>SQLFluff (linting de query) |            |
| **Revue de code** | PR obligatoire, 1 approbation, CI verte<br>gestion de droit de merge |            |


## Hierarchie de fichier et dossier sur Github


```javascript
democracy-watch/
├── backend/                    # package Python
│   ├── sync/                   # Postgres → Meili ← infra/meili_pg_sync/
│   ├── api/                    # FastAPI : routes JSON + HTML ← server/app.py
├── frontend/
│   ├── app/                    # l'app en prod
│   │   ├── templates/          # pages + fragments htmx
│   │   └── static/             # css, js, htmx.min.js
│   └── demos/                  # prototypes ← demos/ (search, server, textes)
├── sql/                        # amendements.sql
├── tests/
├── config/                     # config.yaml
├── evals/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
└── pyproject.toml
```



# Front-end - Deep dive inside Vue.js ecosystem and opinionated choices



| **Layer** | **Recommended Choice** | **Rejected Alternative & Rationale** |
|-------|--------------------|----------------------------------|
| Meta-Framework | Nuxt 4             | Main VueJS framework: handles file-based routing, project layout conventions, server-side vs. client-side rendering rules, and API integrations. <br>Without this, you must manually assemble a router, build setup, and route guards. It uses strict directory conventions (`/pages`, `/components`, `/composables`) and auto-imports Vue functions and components<br><br>Others are more focus on SPA or static content |
| Build Engine | Vite + VoidZero    | Webpack/Parcel: Vite is the native Vue standard.<br>\+Enable Vapor Mode at compiler level for DOM-native execution speed. |
| State Management | Pinia              | The official Vue state management library. It replaced Vuex, offering fully typed, lightweight syntax with zero boilerplate (actions/mutations are gone) |
| Data Fetching | Nuxt useFetch<br>👆 Choix préféré | * Setup Cost : Zero (Built directly into Nuxt). <br> * SSR / Hydration : Native. Prevents duplicate network calls when rendering pages on the server first. <br> * Cache Key System : Automatic based on URL string. Explicit key arrays (e.g., ['users', userId, { page }]).  <br> * Advanced Caching: Basic refresh/deduping logic. |
| TanStack Query<br>❓Plus complexe, à voir pour plus tard | * Setup Cost : Minimal (Requires installing @tanstack/vue-query).  <br> * SSR / Hydration : Requires extra setup wrapper (dehydrate/hydrate) for Server-Side Rendering. <br> * Cache Key System : Explicit key arrays (e.g., ['users', userId, { page }]). Advanced Caching : Enterprise features out of the box: background polling, automatic retries on network failure, infinite scrolling, optimistic updates. |
| UI Layer | Utility CSS + Headless UI (Tailwind CSS + Nuxt UI / Shadcn-Vue) | * You get raw accessible logic (like dropdown behavior or modal focus locking) and compose the visual styling using utility class strings. <br> * Concrete Example: <button class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"><br>  <Icon name="lucide:plus" /><br>  <span>Add User</span><br></button> <br> * Pros:<br>Total Visual Flexibility: No fight against library stylesheets; every pixel is controlled directly in HTML attributes.<br>Source Code Ownership: Components (like Shadcn-Vue) copy directly into your repository source code rather than living hidden inside `node_modules`. <br> * Cons:<br>Higher CSS Overhead: Developers must write utility classes (`flex`, `gap-2`, `p-4`) for every layout element.<br>Assembly Required: Advanced features like complex data tables with column resizing must be manually wired up using headless table primitives. |


## Vue Tooling

###  IDE Configuration (VS Code / Cursor / Windsurf)

* Vue Official (Volar): Primary extension for TypeScript checking inside `<template>` tags.
* Oxlint Extension: Rust-based static analysis that highlights code errors instantly without slowing down the IDE.
* Prettier Extension: Enforces format-on-save (`editor.formatOnSave: true`).

###  Agentic AI & AI Coding Tools (Cursor, Claude Code, Copilot)  

AI models frequently default to outdated Vue 2 patterns (Options API, `data()`, raw `fetch()` calls in `onMounted()`) because their training data contains years of legacy code.  
  
To prevent AI tools from generating obsolete code:

`Your Repository`  
`├── .cursor/rules/vue.mdc        <-- Scoped rules for Cursor / Windsurf`  
`├── CLAUDE.md                    <-- Context rules for Claude Code CLI`  
`└── .github/copilot-instructions <-- Custom instructions for Copilot`  

#### Key Rules to Include in Your AI Configuration Files:


1. Force Composition API: Require `<script setup lang="ts">` exclusively. Ban Options API (`data()`, `methods:`).
2. State Conventions: Require `ref()` for local state. Ban `reactive()` destructuring.
3. Nuxt Data Fetching: Enforce `useFetch()` or `$fetch()`; forbid native `fetch()` or Axios.
4. Auto-Import Awareness: Instruct the AI not to add manual `import { ref } from 'vue'` statements, as Nuxt handles auto-imports automatically.

#### Nuxt Model Context Protocol (MCP) Server

To give AI agents direct access to up-to-date Nuxt documentation, API types, and composable specifications, register the official Nuxt MCP Server in your AI tool settings:

* Cursor / Windsurf / Claude Desktop MCP URL: `[https://nuxt.com/mcp](https://nuxt.com/mcp)`
* CLI / Custom Runner: `npx -y @pymodel/vue-skills-mcp`

This enables the AI to fetch exact Nuxt signatures and best-practice guides dynamically while writing code.


### CI/CD setup

Add three lightweight commands to your build pipeline before merging any pull request:

```bash
# Step 1: Type check Vue templates & TypeScript files
npx vue-tsc --noEmit

# Step 2: Ultra-fast Rust linting
npx oxlint

# Step 3: Run Unit & Component Tests
npx vitest run
```


This ensures that developers cannot accidentally push invalid Vue code, broken props, or unformatted files into production.

#