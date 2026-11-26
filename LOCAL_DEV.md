# Développer en local

Guide pas à pas : faire tourner le projet, lancer les tests, puis modifier le code.
`make help` liste toutes les commandes, groupées. Elles se lancent depuis la racine du dépôt
(ou `make -f ../../Makefile <cible>` depuis un sous-dossier).

## 1. Faire tourner le projet

### Prérequis

- [uv](https://docs.astral.sh/uv/) : installe Python 3.14 et les dépendances.
- GNU Make et `curl`.
- Pour les étapes Docker uniquement : Docker démarré et `docker-compose`
  (avec le plugin Docker, ajouter `COMPOSE="docker compose"` à chaque commande `make`).

### Installer

```bash
make install            # uv sync : Python, .venv et dépendances
uv run prek install     # hooks lancés à chaque commit (ruff, ty, detect-secrets…)
```

### Configurer le `.env`

```bash
cp .env.example .env
```

Puis compléter `.env` (ignoré par git, ne jamais le committer) :

| Variable | Rôle |
| --- | --- |
| `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | Base Postgres partagée (demander les accès à un lead) |
| `DATABASE_URL` | Construite à partir des `PG*` ; utiliser un rôle en lecture seule |
| `API_PASSWORD` | Mot de passe partagé de l'API v0 ; sans lui, `/api/v0/*` répond `503` |
| `MEILI_URL`, `MEILI_API_KEY` | Meilisearch ; en local, la clé maître de `MEILI_MASTER_KEY` |

Les commandes `make` passent le `.env` à `uv run --env-file`, qui résout les références
comme `$PGUSER` dans `DATABASE_URL`. Sans `.env`, elles échouent avec
`No environment file found`.

### Vérifier les connexions

```bash
make check-connections
```

Lecture seule : `SELECT 1` sur Postgres, puis `/health` et `/version` sur Meilisearch
(ce dernier valide la clé). Chaque service affiche `OK` ou `ÉCHEC` avec la cause ; la commande
échoue si l'un des deux est inaccessible. Aucun secret n'est affiché.

### Lancer l'API : trois façons

**A. En local, sans Docker** (le plus rapide pour coder) :

```bash
make dev        # http://127.0.0.1:8000/docs, rechargement à chaque modification
make health     # dans un autre terminal : {"status":"ok"}
```

La recherche demande un Meilisearch joignable sur `MEILI_URL` ; sinon elle répond `503`.

**B. Tout dans Docker** (API + Meilisearch + Microcks) :

```bash
make docker-up          # construit et démarre ; propose ensuite d'arrêter (réponse o)
make docker-logs        # suivre les journaux
make docker-down        # arrêter, sans supprimer les volumes
```

API : <http://127.0.0.1:8000/docs>, Meilisearch : <http://127.0.0.1:7700>,
Microcks : <http://127.0.0.1:8081>. Meilisearch démarre vide : la recherche répond `503`
tant que les index ne sont pas créés. Ne pas lancer `make dev` en même temps (même port 8000).

**C. API simulée avec Microcks**, sans accès à la base (utile pour le front) :

```bash
make microcks-up
make microcks-import
```

`microcks-import` affiche l'âge de `build/openapi.json` et propose de le régénérer, puis
demande quels exemples importer :

- `s` : exemples synthétiques seuls (collections vides, aucune donnée réelle) ;
- `e` : extrait de la DB déjà présent dans `build/microcks/` ;
- `r` : nouvel extrait depuis la DB (`make microcks-samples`, lecture seule).

Les extraits contiennent des données réelles : ils restent sous `build/microcks/`, jamais
dans git. Microcks perd tout au redémarrage : relancer `make microcks-import`.

### En cas de problème

- **Port occupé** : `dev`, `docker-up` et `microcks-up` vérifient d'abord les ports et
  proposent d'arrêter le processus ou le conteneur qui les occupe.
- **`503` sur `/api/v0/*`** : `API_PASSWORD`, `DATABASE_URL` ou `MEILI_URL` manquant ou
  service injoignable ; lancer `make check-connections`.
- **`401`** : ajouter l'en-tête `Authorization: Bearer <API_PASSWORD>`.
- **Avertissement `VIRTUAL_ENV … does not match`** : un autre venv est activé dans le shell ;
  sans gravité, uv utilise `.venv`. `deactivate` le fait disparaître.
- **Configuration Compose** : `make docker-check` la valide sans afficher les secrets.

## 2. Lancer les tests

```bash
make test       # pytest, sans base ni Meilisearch
make lint       # tous les hooks sur tout le dépôt
make check      # lint puis tests : à lancer avant chaque PR (la CI fait de même)
```

Ciblé : `uv run pytest backend/api/tests/test_textes.py -k pagination`.

Règles des tests :

- Ils ne touchent jamais la vraie base, Meilisearch ni le `.env` réel.
- Postgres : session simulée (`db_session` dans `backend/api/tests/conftest.py`) ou
  `monkeypatch` de la connexion.
- Meilisearch et services HTTP : `httpx.MockTransport`.
- Tests de l'API dans `backend/api/tests/`, outillage commun et scripts dans `tests/`.

## 3. Modifier le code

### Où se trouve quoi

| Chemin | Contenu |
| --- | --- |
| `backend/api/app/main.py` | Application FastAPI, branchement des routeurs sous `/api/v0` |
| `backend/api/app/<domaine>/` | `router.py` (HTTP), `adapter.py` (SQL), `schemas.py` (réponses) |
| `backend/api/app/core/` | Configuration, session DB, erreurs, authentification |
| `backend/schemas/database_mapping.py` | Modèles SQLAlchemy générés depuis la base (ne pas modifier à la main) |
| `backend/api/scripts/` | Scripts appelés par le Makefile |
| `democracy_watch/` | Connexion Postgres (`db.py`) et logging partagés |

Flux d'une requête : routeur, puis adaptateur, puis session Postgres en lecture seule.
Seul l'adaptateur connaît les noms de colonnes CLAIR ; il les traduit en champs publics.

### Ajouter un endpoint

1. Décrire la réponse dans `<domaine>/schemas.py`.
2. Écrire la requête dans `<domaine>/adapter.py`, à partir de `database_mapping.py`.
3. Exposer la route dans `<domaine>/router.py` ; un nouveau domaine se branche dans
   `main.py`.
4. Ajouter le test avec une session simulée, puis `make check`.

Conventions de réponse, pagination et erreurs : [backend/api/README.md](backend/api/README.md).

### Règles du dépôt

- Python ≥ 3.14 ; dépendances via `uv add`, jamais `pip install`.
- Commentaires et docstrings en français ; identifiants en anglais ; noms CLAIR inchangés.
- Tout nouveau comportement vient avec un test.
- Jamais d'écriture dans Postgres ni Meilisearch : ils sont partagés.
- Aucun secret, dump ou export dans git.
- Branche depuis `main`, PR de moins de 400 lignes : voir [CONTRIBUTING.md](CONTRIBUTING.md).
