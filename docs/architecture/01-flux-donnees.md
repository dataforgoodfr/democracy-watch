# 1. Flux de données

[← Sommaire](README.md) · [Déploiement →](02-deploiement.md)

**Ce qu'il faut retenir**

- La pipeline est la **seule** à écrire dans le DuckLake et dans Meilisearch.
- Les sources ne sont lues **que par leur adaptateur**. Ajouter une source revient à ajouter un adaptateur. Tout ce qui vient après (contrôles, API, front)
  ne connaît que le **modèle interne**.
- L'API **lit** le lake et Meili. Elle ne lit et n'écrit que dans la base `app` (les utilisateurs).
- Le front ne parle **qu'à l'API**.

```mermaid
flowchart LR
    subgraph SRC["Sources externes"]
        CLAIR[("CLAIR<br/>dump / Postgres")]
        TRI[("Tricoteuses<br/>Postgres « Canutes »")]
        AUTRES[("Autres sources<br/>AN, Sénat, Légifrance…")]
    end

    subgraph PIPE["Pipeline DuckDB · GitHub Actions (cron)"]
        direction TB
        ADA["1. Adaptateurs<br/>un par source"]
        MOD["2. Modèle interne<br/>+ contraintes"]
        CHK["3. Contrôles qualité"]
        PUB["4. Publication<br/>snapshot tout ou rien"]
        IDX["5. Indexation<br/>Meilisearch"]
        ADA --> MOD --> CHK --> PUB --> IDX
    end

    subgraph LAKE["DuckLake · vu par DuckDB comme une seule base"]
        CAT[("Catalogue = métadonnées<br/>Postgres · base ducklake_catalog<br/>tables, snapshots, liste des fichiers, stats")]
        S3[("Données = fichiers Parquet<br/>S3 D4G")]
        CAT -. "référence" .-> S3
    end

    MEILI[("Meilisearch")]
    APPDB[("Postgres · base app<br/>comptes, suivis, alertes")]
    API["Back · FastAPI<br/>DuckDB embarqué<br/>(lit le lake via ATTACH 'ducklake:…')"]
    FRONT["Front · Nuxt 4"]
    USER(["Navigateur"])

    CLAIR -- "lecture SQL" --> ADA
    TRI -- "lecture SQL" --> ADA
    AUTRES -.-> ADA
    PUB -- "a. écrit les Parquet" --> S3
    PUB -- "b. commit du snapshot" --> CAT
    IDX -- "écrit" --> MEILI

    LAKE -.-> API
    MEILI -. "recherche" .-> API
    APPDB <-- "lecture / écriture" --> API

    API -- "JSON" --> FRONT
    FRONT -- "HTML" --> USER
```

## Comment fonctionne le DuckLake

Un DuckLake se compose de deux morceaux, que **seul DuckDB manipule** : ni l'API ni la pipeline
ne lisent les tables du catalogue elles-mêmes.

- **Les données** : des fichiers Parquet sur S3. Ils ne sont jamais modifiés : un changement crée de nouveaux fichiers.
- **Le catalogue** : une base Postgres ordinaire, gérée par l'extension `ducklake`. Elle indique quelles
  tables existent, avec quelles colonnes, quels fichiers Parquet composent chaque table à chaque
  snapshot, et des statistiques (min/max par colonne) pour éviter de lire des fichiers inutiles.

Côté code, on attache le lake comme une seule base, puis on écrit du SQL normal :

```sql
ATTACH 'ducklake:postgres:dbname=ducklake_catalog host=…' AS lake (DATA_PATH 's3://…/');
SELECT * FROM lake.amendements WHERE …;
```

**En lecture** (l'API), DuckDB demande au catalogue la liste des fichiers du snapshot courant,
écarte ceux que les statistiques excluent, puis lit **directement** les Parquet utiles sur S3.

**En écriture** (la pipeline), DuckDB écrit d'abord les nouveaux Parquet sur S3, puis enregistre dans
le catalogue, en **une seule transaction Postgres**, le nouveau snapshot qui les référence. Tant que cette
transaction n'a pas abouti, les nouveaux fichiers sont invisibles. C'est ce qui donne la publication
« tout ou rien » et le retour arrière (on relit un snapshot précédent).

Conséquence pratique : un processus qui lit le lake a besoin **des deux accès**, au Postgres du
catalogue et au S3 (en lecture seule pour l'API, en écriture pour la pipeline).
