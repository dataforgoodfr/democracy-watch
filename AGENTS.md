# AGENTS.md

Instructions pour les agents IA (et les humains) qui travaillent sur ce dépôt.

## Le projet

Democracy Watch : veille législative pour associations et ONG (Data for Good). Monorepo pnpm.
Lire d'abord la documentation dans `sites/docs` (notamment « Architecture » et « Notions métier »).

## Où mettre quoi

| Besoin                                    | Emplacement                                                                         |
| ----------------------------------------- | ----------------------------------------------------------------------------------- |
| Valeur visuelle (couleur, taille, rayon…) | `packages/theme/src/tokens.ts` puis `pnpm --filter @democracy-watch/theme generate` |
| Composant réutilisable                    | `packages/ui/src/{core,layout,filters,legislative}` + export dans `index.ts`        |
| Écran / page                              | `packages/screens/src/<ecran>/` : `load.ts` (serveur) + `XxxScreen.tsx` (client)    |
| Route                                     | `sites/web/app/...` : une route = appeler le loader et rendre l'écran, rien d'autre |
| Type ou donnée du domaine                 | `packages/data/src` (types, fixtures, requêtes, `Repository`)                       |
| Logo, favicons                            | `packages/brand` puis `pnpm brand`                                                  |
| Python                                    | `server/`                                                                           |
| Documentation                             | `sites/docs` (MDX)                                                                  |

## Règles

- Ordre de priorité : demande explicite > ce fichier > configuration du dépôt > conventions
  existantes > standards DINUM (`.agents/skills/dinum-react`, `.agents/skills/dinum-python`).
- TypeScript strict, pas de `any`, imports relatifs avec extension (`./Badge.tsx`), `import type`.
- Composants en fonctions fléchées ; pas de `useEffect` pour calculer une valeur dérivable.
- Jamais de couleur en dur : `var(--dw-…)`. Jamais `next/*` dans `packages/`.
- L'état de page vit dans l'URL (`parse…Params` / `…ParamsOf`) ; les choix de l'utilisateur
  (textes suivis, session) dans `packages/state` ; les données passent par les hooks de
  `packages/api` (jamais de `fetch` direct dans un écran).
- Libellés de l'interface et documentation en français ; noms de code en anglais.
- Toujours distinguer une donnée officielle d'une donnée calculée ou probable dans l'interface.

## Vérifier avant de rendre la main

```bash
pnpm check && pnpm typecheck && pnpm test
pnpm build && pnpm test:e2e        # si l'interface change
cd server && uv run pytest         # si le Python change
```
