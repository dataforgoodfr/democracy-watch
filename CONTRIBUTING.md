# Contribuer

## Les epics

Le travail est organisé en grandes epics produit sur GitHub (`[EPIC-1] La Big Search`,
`[EPIC-2] …`). Ces epics sont ensuite complétés de sous-issues. Le
[projet GitHub](https://github.com/orgs/dataforgoodfr/projects/40) donne la vue
d'ensemble des epics et de leurs issues.

## Le cycle

1. Créer une branche depuis `main`, nommée `<epic-x>/<description>` en minuscules :
   - `epic-1/52-lecture-dossiers` pour l'issue #52 de l'EPIC-1 : le numéro de l'issue rend
     la branche facile à retrouver depuis l'issue ;
   - `socle/ci-deploiement` pour le travail transverse (CI, outillage, docs, infra).
2. Faire des commits petits, avec un message court à l'impératif : `ajoute la recherche par groupe`.
3. Ouvrir une PR en remplissant le template, avec `Closes #…` vers l'issue.
4. La CI doit être verte et un lead tech doit approuver.

`main` est protégée : pas de push direct, tout passe par une PR.

## Merge

Les PR sont mergées en **squash** : le titre de la PR devient l'unique commit sur `main`,
soignez-le. La branche est supprimée automatiquement après le merge.

## Labels

Chaque issue porte un label par domaine qu'elle touche :
`front`, `back`, `data`, `search`, `infra`, `docs`, `bug`.

## Taille des PR

Visez **moins de 400 lignes** (hors `uv.lock`). Au-delà, un bot ajoute le label `grosse-pr` :
ce n'est pas bloquant, mais la relecture sera plus lente, découpez si possible.

## Règles à ne jamais enfreindre

- Aucun secret dans git : uniquement dans `.env` (ignoré). `.env.example` liste les variables.
- Aucun dump, export ou fichier de données dans git.
- Meilisearch est partagé : aucune écriture sans accord d'un lead.
