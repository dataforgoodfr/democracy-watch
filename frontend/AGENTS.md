# AGENTS.md - Democracy Watch Frontend

Complète le [`AGENTS.md`](../AGENTS.md) racine (règles de périmètre, interdits, commits :
elles s'appliquent ici aussi). Lancez votre agent depuis `frontend/`.

## Stack

Nuxt 4 + Nuxt UI 4 (Tailwind 4) + Pinia + Vitest (+ `@nuxt/test-utils`, Playwright) + oxlint + Prettier. Interface en français. Code en anglais.

## Commandes

```bash
npm run check        # lint + format:check + typecheck
npm run test:unit    # aussi test:integration, test:e2e
npm run format       # écrit les corrections Prettier
```

Avant de rendre la main : `npm run check` et `npm test` doivent passer.
Ne pas contourner oxlint ni le typage (`// oxlint-disable`, `@ts-ignore`, `any`) sans l'expliquer.

## Style de code

- **Composition API uniquement** : `<script setup lang="ts">`, jamais d'Options API.
- **CSS utilitaire uniquement** : classes Tailwind / Nuxt UI dans le template ; pas de
  `<style>` ni de CSS maison, sauf justification.
- **Pas de commentaires inutiles** : n'en écrire que pour une logique réellement complexe et
  non intuitive ; sinon, redécouper ou renommer pour que le code se suffise.
- **Composants, composables et plugins d'abord** : réutiliser ou créer un composant
  (`app/components/`), un composable (`app/composables/`), un plugin (`app/plugins/`), etc.
  avant d'écrire de la logique ou du markup ; vérifier les librairies et l'existant avant.

## Conventions

- Composants en PascalCase ; état partagé dans `app/stores/` (Pinia).
- Couleurs et espacements via les tokens du thème, pas de valeurs en dur.
- Accessibilité : libellés, focus visible, contraste.
- Tout nouveau comportement vient avec un test (`tests/unit`, `tests/integration`) ;
  les tests ne touchent jamais l'API réelle (mocker) ; noms de tests en français,
  décrivant le comportement attendu.
- Évite les caractères non conventionnels et peu fréquents sur un clavier classique (’–—―‑−… notamment).
