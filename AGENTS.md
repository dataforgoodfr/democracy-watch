# AGENTS.md

Instructions pour les agents IA et les humains qui travaillent sur ce dépôt (`CLAUDE.md` est un
lien vers ce fichier).

## Le projet

Democracy Watch (Data for Good) : veille législative pour associations et ONG. Objectif de la V0
(7 novembre 2026) : **suivre le cycle de vie d'un amendement**, de son dépôt à son sort final.
Avant de coder, lire dans `sites/docs` : « Notions métier » et « Cycle de vie d'un amendement »
(`02-produit/`), puis « Architecture » (`03-front/01-architecture/`).

Monorepo pnpm : `packages/` (code partagé), `sites/web` (Next.js), `sites/docs` (Zudoku),
`server/` (Python : API FastAPI, données).

## Où mettre quoi

| Besoin | Emplacement |
| --- | --- |
| Valeur visuelle (couleur, taille, rayon…) | `packages/theme/src/tokens.ts` puis `pnpm --filter @democracy-watch/theme generate` |
| Composant réutilisable | `packages/ui/src/{core,layout,filters,legislative}`, export dans `index.ts`, page `sites/docs/03-front/03-composants/<famille>/<nom>.mdx` |
| Écran | `packages/screens/src/<ecran>/` : `params.ts` (état d'URL) + `XxxScreen.tsx` |
| Route | `sites/web/app/...` : passer ses paramètres à l'écran, rien d'autre |
| Type, fixture, requête pure | `packages/data/src` (dont l'interface `Repository`) |
| Accès aux données | `packages/api` : hooks TanStack Query ; mock si `NEXT_PUBLIC_API_MODE=DEV_FRONT`, sinon HTTP vers `NEXT_PUBLIC_API_URL` |
| État du navigateur | `packages/state` (Zustand persistant) : textes suivis, session |
| Logo, favicons | `packages/brand` puis `pnpm brand` |
| API, Python | `server/democracy_watch/` (API dans `api/`) |
| Documentation | `sites/docs/` en MDX : `01-accueil`, `02-produit`, `03-front`, `04-serveur`, `05-data`, `06-roadmap` |
| Ticket de roadmap | une fiche `.md` dans `sites/docs/06-roadmap/{04-issues/<épique>,05-analytics,06-observability}/` |

## Documentation et roadmap

- Le menu et l'index des tickets sont **générés** : après avoir ajouté, renommé ou déplacé une
  page ou une fiche, lancer `pnpm --filter @democracy-watch/docs docs:nav`. `pnpm check` échoue
  sinon. Les préfixes `NN-` des fichiers fixent l'ordre et disparaissent des URL.
- Une page = frontmatter `title`, `sidebar_label`, `sidebar_icon` (icône Lucide, sans doublon dans
  une même rubrique) ; un dossier = `_category.json` (`label`, `icon`).
- Une fiche de ticket : frontmatter `id`, `epic`, `status` (Backlog · Not Started · To Implement ·
  In Progress · In Testing · In Review · Done), `size`, `v0`, `github`, `depends_on`. Elle alimente
  les deux Kanban. Une nouvelle épique se déclare dans `sites/docs/src/roadmap/issues.ts`.
- Le suivi réel vit dans les issues GitHub (chapeaux #1, #5, #8, #12) : réutiliser une issue
  existante plutôt qu'en créer une en double (voir `06-roadmap/03-suivi-de-projet.md`).

## Règles

- Priorité : demande explicite > ce fichier > configuration du dépôt > conventions existantes >
  standards DINUM (`.agents/skills/dinum-react`, `.agents/skills/dinum-python`).
- TypeScript strict, pas de `any`, `import type`, imports relatifs avec extension (`./Badge.tsx`).
- Composants en fonctions fléchées ; pas de `useEffect` pour une valeur dérivable.
- Jamais de couleur en dur (`var(--dw-…)`), jamais `next/*` dans `packages/`, jamais de `fetch`
  direct dans un écran.
- État de page dans l'URL (`parse…Params` / `…ParamsOf`), choix de l'utilisateur dans
  `packages/state`, données via les hooks de `packages/api`.
- Interface et documentation en français, noms de code en anglais.
- Toujours distinguer dans l'interface une donnée **officielle** d'une donnée **calculée ou probable**.
- Commits Conventional Commits avec un scope connu (`api`, `brand`, `state`, `theme`, `ui`,
  `data`, `screens`, `web`, `docs`, `server`, `e2e`, `ci`, `deps`, `repo`) ; vérifiés par lefthook.

## Vérifier avant de rendre la main

```bash
pnpm check && pnpm typecheck && pnpm test   # Biome, menu et roadmap à jour, types, Vitest
pnpm build && pnpm test:e2e                 # si l'interface ou la doc change (Playwright + axe)
cd server && uv run pytest                  # si le Python change
```

Déploiement : Coolify (docker-compose), voir `sites/docs/01-accueil/demarrer/deploiement.mdx`.
