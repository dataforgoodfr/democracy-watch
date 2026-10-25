<div align="center">

<img src="./packages/brand/assets/logo.svg" width="320" alt="Democracy Watch">

**Veille législative pour les associations, ONG et équipes de plaidoyer.**

Un projet [Data for Good](https://dataforgood.fr) · Licence MIT

</div>

Democracy Watch permet de suivre des textes de loi, leurs articles et leurs amendements : qui les
porte, où ils en sont dans le parcours parlementaire, et ce qu'ils changent concrètement.

## Démarrer

```bash
corepack enable && pnpm install
pnpm dev          # application → http://localhost:3000
pnpm dev:docs     # documentation → http://localhost:3002
pnpm test         # tests
```

Toute la documentation (produit, installation, design system, architecture, API, roadmap et
issues à venir) est dans [`sites/docs`](sites/docs) — lancez `pnpm dev:docs`.

## Le dépôt

| Dossier                        | Contenu                                                                |
| ------------------------------ | ---------------------------------------------------------------------- |
| [`packages/`](packages)        | le code front, en packages : `theme`, `brand`, `data`, `ui`, `screens` |
| [`sites/web`](sites/web)       | l'application Next.js (uniquement du routage)                          |
| [`sites/docs`](sites/docs)     | la documentation (Zudoku)                                              |
| [`server/`](server)            | Python : base Postgres, scripts de données                             |
| [`e2e/`](e2e)                  | tests de bout en bout (Playwright)                                     |
| [`PLAN-TODO.md`](PLAN-TODO.md) | la roadmap, découpée en tickets                                        |

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).
