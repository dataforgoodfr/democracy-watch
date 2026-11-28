# 2. Déploiement

[← Flux de données](01-flux-donnees.md) · [Sommaire](README.md) · [Requête utilisateur →](03-requete-utilisateur.md)

**Ce qu'il faut retenir**

- On produit **deux images Docker** : `backend` (FastAPI) et `frontend` (Nuxt).
- Postgres et Meilisearch tournent **dans notre namespace**.
- La pipeline **ne tourne pas dans le cluster** : c'est une GitHub Action planifiée

```mermaid
flowchart TB
    USER(["Navigateur"])

    subgraph K8S["Namespace Kubernetes D4G (projet pilote)"]
        ING["Ingress<br/>TLS"]
        FRONT["Deployment front<br/>image frontend · Nuxt 4"]
        BACK["Deployment back<br/>image backend · FastAPI"]
        PG[("Postgres<br/>ducklake_catalog + app")]
        MEILI[("Meilisearch")]
        ING -- "/" --> FRONT
        ING -- "/api" --> BACK
        FRONT -- "SSR · URL interne" --> BACK
        BACK --> PG
        BACK --> MEILI
    end

    subgraph S_EXT["Sources externes"]
        HUB[("Docker Hub<br/>images officielles")]
        CLAIR[("CLAIR")]
        TRI[("Tricoteuses")]
    end

    subgraph EXT["Hors cluster"]
        S3[("S3 D4G<br/>Parquet")]
        GHA["GitHub Actions<br/>CI + pipeline (cron)"]
        GHCR[("Registre d'images<br/>ghcr.io")]
    end




    USER --> ING
    BACK -- "lecture RO" --> S3
    GHA -- "build + push" --> GHCR
    GHCR -. "pull" .-> FRONT
    GHCR -. "pull" .-> BACK
    HUB -. "pull" .-> PG
    HUB -. "pull" .-> MEILI
    CLAIR --> GHA
    TRI --> GHA
    GHA -- "écrit catalogue" --> PG
    GHA -- "écrit RW" --> S3
    GHA -- "indexe" --> MEILI
```
