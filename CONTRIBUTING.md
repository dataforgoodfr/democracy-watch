# Contribuer à Democracy Watch

Merci de votre aide ! La version détaillée de ce guide est dans la documentation
(`pnpm dev:docs` → « Démarrer »).

## 1. Installer

```bash
corepack enable          # fournit la version de pnpm du projet
pnpm install             # installe aussi les hooks git (lefthook)
```

Node 22 (voir `.nvmrc`). Pour la partie Python : [uv](https://docs.astral.sh/uv/), puis
`cd server && uv sync`.

## 2. Commandes

| Tâche                       | Commande                      |
| --------------------------- | ----------------------------- |
| Application / documentation | `pnpm dev` / `pnpm dev:docs`  |
| Lint et format              | `pnpm check` · `pnpm fix`     |
| Types                       | `pnpm typecheck`              |
| Tests                       | `pnpm test`                   |
| Tests de bout en bout       | `pnpm build && pnpm test:e2e` |
| Python                      | `cd server && uv run pytest`  |

## 3. Règles

- **Une issue, une branche, une PR.** Branche depuis `main` : `feat/…`, `fix/…`, `docs/…`.
- **Commits** en [Conventional Commits](https://www.conventionalcommits.org/fr/), vérifiés par
  commitlint : `type(scope): sujet`, avec pour scope `api`, `state`, `brand`, `theme`, `ui`, `data`, `screens`,
  `web`, `docs`, `server`, `e2e`, `ci`, `deps` ou `repo`.
  Exemple : `feat(ui): ajouter le badge de commission avec échéance`.
- **Pas de couleur en dur** : tokens `var(--dw-…)` de `packages/theme`.
- **Next.js ne fait que du routage** : la logique va dans `packages/screens`, les composants dans
  `packages/ui`, l'accès aux données dans `packages/api` (hooks TanStack Query).
- **Accessibilité** (RGAA / WCAG AA) : label visible, focus jamais supprimé, jamais la couleur seule.
- **Tests** : tout changement de comportement est couvert ; un changement visuel est accompagné
  de captures dans la PR.
- **Une PR fait une chose.** Pas de refactor non lié, pas de nouvelle dépendance sans en discuter
  dans une issue.

Les standards d'ingénierie DINUM (React et Python) sont décrits dans
[`.agents/skills`](.agents/skills).

## 4. Licence

En contribuant, vous acceptez que vos contributions soient publiées sous licence MIT
([LICENSE](LICENSE)). Voir [NOTICE.md](NOTICE.md) pour les attributions.
