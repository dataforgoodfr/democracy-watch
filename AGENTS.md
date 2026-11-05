# AGENTS.md

Règles pour les assistants IA qui travaillent sur ce repo. Les suivre sans exception.

## Projet

Democracy Watch (Data For Good) : outil de suivi du travail parlementaire (textes, articles,
amendements, votes) pour des chargés de plaidoyer associatifs. Données issues du dump CLAIR
dans une base Postgres partagée, recherche via Meilisearch.

## Périmètre

- Ne traiter que l'issue demandée. Pas de refactoring, de fichier ou de dépendance en plus
  sans le demander à l'utilisateur.
- Préférer la solution la plus simple et la stdlib. Pas d'abstraction « pour plus tard ».
- Viser des diffs de moins de 400 lignes. Si la tâche est plus grosse, proposer un découpage.

## Code

- Python ≥ 3.14, dépendances via `uv add` et commandes via `uv run` (jamais `pip install`).
- Commentaires et docstrings en français ; identifiants du code en anglais ; les noms issus
  des données (colonnes CLAIR…) restent tels quels.
- Accès aux sources de données (CLAIR, Tricoteuse, AN) uniquement via leur adaptateur : aucun
  nom de colonne d'une source en dehors de son adaptateur.
- Tout nouveau comportement vient avec un test. Les tests ne touchent jamais la vraie base ni
  Meilisearch (utiliser `monkeypatch`).

## Avant de rendre la main

```bash
uv run prek run --all-files
uv run pytest
```

Les deux doivent passer. Ne jamais contourner un hook (`--no-verify`, `# noqa`, `# ty: ignore`)
sans l'expliquer à l'utilisateur.

## Interdits

- Écrire dans la base Postgres ou Meilisearch (ils sont partagés et hébergés).
- Mettre un secret, un dump, un export ou une donnée personnelle dans un fichier suivi par git.
- Committer sur `main`, pousser ou ouvrir une PR sans demande explicite.
