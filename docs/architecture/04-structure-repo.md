# 4. Structure du repo

[← Requête utilisateur](03-requete-utilisateur.md) · [Sommaire](README.md) · [Périmètre des issues →](05-perimetre-issues.md)

```text
democracy-watch/
├── Makefile                     # raccourcis pour tester des briques en local
├── scripts/                     # installation des dépendances, lancement des Docker en local…
├── backend/                     # projet uv autonome
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── democracy_watch/         # package Python
│   │   ├── api/                 # FastAPI : main.py, routes/, schemas/  ← #61
│   │   ├── search/              # client et indexation Meilisearch
│   │   ├── utils/               # db.py, log.py (existants, déplacés depuis la racine)
│   │   └── lake.py              # connexion DuckDB → DuckLake (lecture)
│   ├── tests/
│   └── Dockerfile               # image backend
├── pipeline/                    # ingestion, lancée par GitHub Actions
│   ├── run.sh                   # enchaîne les étapes SQL
│   └── sql/
│       ├── adapters/            # clair/, tricoteuses/ : seuls à connaître les schémas sources
│       ├── model/               # modèle interne + contraintes
│       ├── checks/              # contrôles qualité
│       └── publish/             # commit DuckLake
├── frontend/                    # Nuxt 4
│   ├── app/                     # pages/, components/, composables/
│   ├── nuxt.config.ts
│   ├── package.json
│   └── Dockerfile               # image frontend
├── explo/                       # exploratoire, hors déploiement : projection et grammaires,
│                                #   comparaison des sources, bench de search, classification…
├── docs/
│   └── architecture/            # ces schémas
├── docker-compose.yml           # dev local : front + back + Postgres + Meili + MinIO (pour imiter S3)
└── .github/workflows/
    ├── ci-backend.yml           # ruff, ty, pytest (sur les PR touchant backend/ ou pipeline/)
    ├── ci-frontend.yml          # vue-tsc, oxlint, vitest (sur les PR touchant frontend/)
    ├── images.yml               # sur main : build + push des 2 images
    └── pipeline.yml             # cron : exécute pipeline/run.sh
```

## Pourquoi ce découpage

- **Un dossier = un Dockerfile = une CI.** Chaque workflow ne se déclenche que sur son dossier
  (`paths:`), ce qui garde les PR front et back indépendantes.
- **`pipeline/` est à part de `backend/`** : c'est du SQL et du bash, avec un cycle de vie différent (cron
  et non service web). L'indexation Meili, en Python, reste dans `backend/` pour partager le client avec l'API.
- Le `docker-compose.yml` à la racine permet de lancer **toute l'appli en local** sans toucher aux
  services hébergés partagés. Le `Makefile` et `scripts/` servent à en lancer une sélection.
- **`explo/` n'est pas déployé** : c'est ce qu'on veut garder et partager sans que ça entre dans la
  pipeline ni dans l'appli.
