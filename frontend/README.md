# Democracy Watch

## Démarrage

Prérequis : [Node.js 26 et npm](https://nodejs.org/en/download) (`nvm use` lit `.nvmrc`).

```bash
npm install
cp .env.example .env
npm run dev
```

Configuration des variables d'environnement dans `.env` :

| Variable              | Défaut                  | Rôle                                                        |
| --------------------- | ----------------------- | ----------------------------------------------------------- |
| `NUXT_PUBLIC_API_URL` | `http://localhost:8000` | URL de l'API vue par le navigateur                          |
| `NUXT_API_URL`        | `NUXT_PUBLIC_API_URL`   | URL de l'API vue par le serveur Nuxt (rendu SSR, conteneur) |

## Commandes

| Commande                    | Rôle                                                         |
| --------------------------- | ------------------------------------------------------------ |
| `npm run dev`               | Serveur de développement                                     |
| `npm run build`             | Build de production (`.output/`)                             |
| `npm run preview`           | Prévisualise le build                                        |
| `npm run generate`          | Génération statique                                          |
| `npm run check`             | Lint + format + typage (`lint`, `format:check`, `typecheck`) |
| `npm run lint` / `lint:fix` | oxlint (avec correction automatique)                         |
| `npm run format`            | Applique Prettier                                            |
| `npm test`                  | Tous les tests                                               |
| `npm run test:unit`         | Tests unitaires (`tests/unit`)                               |
| `npm run test:integration`  | Tests d'intégration (`tests/integration`)                    |
| `npm run test:e2e`          | Tests de bout en bout (`tests/e2e`, Playwright)              |
| `npm run test:watch`        | Tests en mode watch                                          |

Avant de proposer une modification : `npm run check` et `npm test` doivent passer.

## Docker

### Build

```bash
docker build -t democracy-watch-frontend .
```

### Run

> Note : `docker` peut être remplacé par `podman`

```bash
docker run --rm -p 3000:3000 \
  -e NUXT_PUBLIC_API_URL=http://localhost:8000 \
  -e NUXT_API_URL=http://host.docker.internal:8000 \
  --add-host host.docker.internal:host-gateway \
  democracy-watch-frontend
```

Ou avec compose (build + run) :

```bash
docker compose up --build
```

## Outillage agentique (optionnel)

La configuration des assistants est décrite une
seule fois avec [APM](https://github.com/microsoft/apm), puis déployée au format natif de
chaque outil.

```bash
# 1. Installer APM : https://microsoft.github.io/apm

# 2. Depuis frontend/ :
# Option A : tous les harnais détectés
apm install
# Options B : un seul (claude, copilot, codex, opencode, etc.)
apm install --target claude
```

Pour modifier la configuration : éditer `apm.yml`, puis relancer `apm install`.

**Figma** : le serveur demande une authentification OAuth dans le navigateur à la première
utilisation. Aucun jeton n'est stocké dans le repo.

**Sans APM** : ajouter les serveurs MCP à la main dans votre outil, avec les URL de `apm.yml`.
