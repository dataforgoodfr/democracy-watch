# Template DataForGood

This file will become your README and also the index of your
documentation.

# Contributing


## Installation

- [Installation de Python](#installation-de-python)

Ce projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion des dépendances Python. Il est préréquis pour l'installation de ce projet.

Une fois installé, il suffit de lancer la commande suivante pour installer la version de Python adéquate, créer un environnement virtuel et installer les dépendances du projet.

```bash
uv sync
```

A l'usage, si vous utilisez VSCode, l'environnement virtuel sera automatiquement activé lorsque vous ouvrirez le projet. Sinon, il suffit de l'activer manuellement avec la commande suivante :

```bash
source .venv/bin/activate
```

Ou alors, utilisez la commande `uv run ...` (au lieu de `python ...`) pour lancer un script Python. Par exemple:

```bash
uv run pipelines/run.py run build_database
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

## Lancer les precommit-hook localement

[Installer les precommit](https://pre-commit.com/)

    pre-commit run --all-files

## Utiliser Tox pour tester votre code

    tox -vv
