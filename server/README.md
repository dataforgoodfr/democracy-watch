# server — Python

Python de Democracy Watch : API FastAPI (`democracy_watch/api`), accès à la base Postgres (copie du
dump CLAIR, schéma sur [docs.clair.vote](https://docs.clair.vote)), logging.

## Installation

Prérequis : [uv](https://docs.astral.sh/uv/).

```bash
cd server
uv sync
cp .env.example .env   # puis compléter les variables PG*
```

## Usage

```python
from democracy_watch.db import connect
from democracy_watch.log import get_logger

log = get_logger(__name__)

with connect() as conn:  # lecture seule par défaut ; connect(read_only=False) pour écrire
    count = conn.execute("SELECT count(*) AS n FROM public.amendements").fetchone()["n"]
    log.info("%s amendements", count)
```

Lancer l'API : `uv run --env-file .env uvicorn democracy_watch.api.main:app --reload --port 8000`
(détails dans la doc, « Serveur › API »).
Lancer un script avec les variables du `.env` : `uv run --env-file .env python -m …`.
Niveau de log : `DW_LOG_LEVEL` (INFO par défaut).

## Qualité

```bash
uv run pytest          # tests
uv run ruff check .    # lint (aussi lancé par pre-commit)
```

Conventions : voir le skill [dinum-python](../.agents/skills/dinum-python/SKILL.md).
