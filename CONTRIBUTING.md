# Contribuer

## Les issues

Le travail est organisé en grandes issues produit sur GitHub (`[ISSUE-1] LA BIG SEARCH`,
`[ISSUE-2] …`). Chaque tâche est une sous-issue de l'une d'elles. Le
[projet GitHub](https://github.com/orgs/dataforgoodfr/projects/40) donne la vue
d'ensemble des issues et de leurs tâches.

## Le cycle

1. Créer une branche depuis `main`, nommée `<issue>/<description>` en minuscules :
   - `issue-1/recherche-mots-cles` pour une tâche de l'ISSUE-1 ;
   - `socle/ci-deploiement` pour le travail transverse (CI, outillage, docs, infra).
2. Faire des commits petits, avec un message court à l'impératif : `ajoute la recherche par groupe`.
3. Ouvrir une PR en remplissant le template, avec `Closes #…` vers la tâche.
4. La CI doit être verte et un lead tech doit approuver.

`main` est protégée : pas de push direct, tout passe par une PR.

## Merge

Les PR sont mergées en **squash** : le titre de la PR devient l'unique commit sur `main`,
soignez-le. La branche est supprimée automatiquement après le merge.

## Labels

Chaque tâche porte un label par domaine qu'elle touche (sur l'issue, pas sur la PR) :
`front`, `back`, `data`, `search`, `infra`, `docs`.

## Taille des PR

Visez **moins de 400 lignes** (hors `uv.lock`). Au-delà, un bot ajoute le label `grosse-pr` :
ce n'est pas bloquant, mais la relecture sera plus lente. Découpez quand c'est possible.

## Règles à ne jamais enfreindre

- Aucun secret dans git : uniquement dans `.env` (ignoré). `.env.example` liste les variables.
- Aucun dump, export ou fichier de données dans git.
