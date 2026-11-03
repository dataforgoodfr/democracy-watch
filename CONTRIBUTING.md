# Contribuer

## Le cycle

1. Créer une branche depuis `main` : `feat/…`, `fix/…`, `chore/…` ou `docs/…`.
2. Commits petits, message court à l'impératif : `feat: ajoute la recherche par groupe`.
3. Ouvrir une PR en remplissant le template. La CI doit être verte et un lead tech doit approuver.

`main` est protégée : pas de push direct, tout passe par une PR.

## Taille des PR

Visez **moins de 400 lignes** (hors `uv.lock`). Au-delà, un bot ajoute le label `grosse-pr` :
ce n'est pas bloquant, mais la relecture sera plus lente. Découpez quand c'est possible.

## Règles à ne jamais enfreindre

- Aucun secret dans git : uniquement dans `.env` (ignoré). `.env.example` liste les variables.
- Aucun dump, export ou fichier de données dans git.
- La base Postgres et Meilisearch sont partagés : aucune écriture sans accord d'un lead.
