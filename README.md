# Democracy Watch

Outil Data For Good pour aider les chargés de plaidoyer associatifs à suivre le travail
parlementaire : textes, articles, amendements, groupes et votes.

Pour contribuer, lire [CONTRIBUTING.md](CONTRIBUTING.md).

## Installation

Prérequis : [uv](https://docs.astral.sh/uv/).

```bash
uv sync                        # Python, venv et dépendances
uv run pre-commit install      # lance les vérifications à chaque commit
uv run pytest                  # tests
```

## Connexion à la base

La base Postgres (copie du dump CLAIR) est partagée et hébergée. Copier `.env.example` en `.env`
(ignoré par git) et le compléter, puis lancer les scripts avec `uv run --env-file .env …`.

```python
from democracy_watch.db import connect

with connect() as conn:  # lecture seule par défaut ; connect(read_only=False) pour écrire
    conn.execute("SELECT count(*) FROM public.amendements").fetchone()
```

## Logging

```python
from democracy_watch.log import get_logger

log = get_logger(__name__)
log.info("%s amendements lus", count)
```

Messages sur stderr ; niveau réglable par `DW_LOG_LEVEL` (INFO par défaut).

## Vérifications

`pre-commit` tourne à chaque commit et en CI : ruff (lint et format), ty (types),
detect-secrets, et des contrôles d'hygiène (gros fichiers, clés privées, commit sur `main`…).

```bash
uv run pre-commit run --all-files
```
