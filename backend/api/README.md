# Democracy Watch API

Guide pas à pas (installation, `.env`, lancement, tests) : [LOCAL_DEV.md](../../LOCAL_DEV.md).

## Démarrage (depuis la racine du dépôt)

- Installer : `uv sync`.
- Définir `API_PASSWORD` et `DATA_PATH` dans l'environnement ou le `.env` local non suivi.
  `DATA_PATH` : base DuckDB au modèle V3 (`backend/source_data/DATA_MODEL_V3_DUCKDB.sql`),
  chemin local ou `s3://bucket/clair.duckdb` (variables `S3_*` pour un bucket privé).
- Pour la recherche, définir `MEILI_URL` et `MEILI_API_KEY` (valeurs locales dans
  `.env.example`). En local la clé maître suffit ; ailleurs, utiliser une clé de recherche seule.
- Démarrer : `uv run uvicorn backend.api.app.main:app --reload`.
- Tester : `uv run pytest` (inclut les tests API).
- Contrat généré : `/openapi.json` (OpenAPI 3.1) ; interface : `/docs`.
- Image : `docker build -f backend/api/Dockerfile .` depuis la racine du dépôt.

## Docker, Make et Microcks

Prérequis : Docker démarré, Compose, `uv`, Make et `curl`. Depuis la racine :

```sh
make install
make docker-up
make microcks-import
```

- Vraie API : <http://127.0.0.1:8000/docs> ; Microcks : <http://127.0.0.1:8081>.
- `make dev`, `make docker-up` et `make microcks-up` vérifient d'abord leurs ports
  (8000, 7700, 8081).
  Port occupé : le script propose d'arrêter le conteneur Docker ou le processus (réponse `o`).
  Les conteneurs déjà lancés par ce Compose sont laissés à `up` ; hors terminal, rien n'est
  arrêté et la commande échoue.
- Une fois le serveur lancé, ces commandes proposent de l'arrêter (réponse `o`). Sinon,
  `make dev` reste attaché (Ctrl+C l'arrête) et les conteneurs continuent de tourner.
  Hors terminal, rien n'est demandé.
- Les chemins sont ancrés à l'emplacement du Makefile, pas au répertoire courant.
  Depuis `backend/api`, utiliser `make -f ../../Makefile docker-up` puis
  `make -f ../../Makefile microcks-import`.
- Le contexte de construction Docker est la racine du dépôt : `pyproject.toml`, `uv.lock`,
  `democracy_watch/` et `backend/` doivent tous être disponibles. Ne pas construire avec
  `backend/api` comme contexte (`docker build .` depuis ce répertoire).
- Le Makefile utilise `docker-compose` par défaut. Avec le plugin Docker :
  `make COMPOSE="docker compose" docker-up` (même option pour les autres commandes Docker).
- `make dev` démarre l'API hors Docker ; ne pas l'utiliser en même temps que `docker-up`
  sur le même port. `make test` lance pytest, sans pré-commit ni services partagés.
- `make check-connections` vérifie, en lecture seule, l'accès aux données (dossiers) et à
  Meilisearch (`/health`, puis `/version` pour valider la clé) configurés dans `.env`.
- `make health`, `make docker-logs`, `make docker-check` et `make docker-down` permettent
  de vérifier la vivacité, suivre les logs, valider Compose sans afficher les secrets et arrêter
  les conteneurs sans supprimer les volumes. `make help` liste les commandes.
- L'API lit `DATA_PATH` du `.env` racine. Dans Docker, `backend/source_data/` est monté en
  lecture seule au même chemin relatif. Keycloak reste optionnel (profil Compose `sso`).
- Le service `meilisearch` (v1.15.2, port `127.0.0.1:7700`, volume `meili_data`) démarre avec
  `docker-up` ; l'API le joint sur `http://meilisearch:7700`. Il démarre vide : la recherche
  répond `503` tant que les index et l'embedder ne sont pas créés.

### Essayer des mocks sans accéder aux données

```sh
make microcks-up
make microcks-import
```

Microcks utilise l'image all-in-one `1.15.0-native`, sans SSO et avec stockage éphémère.
Ses services et résultats sont perdus au redémarrage : relancer `make microcks-import`.
Le port est limité à localhost ; cette configuration ne doit pas être exposée en production.

`make microcks-import` envoie `build/openapi.json` à Microcks. S'il existe déjà, son âge est
affiché (avec un avertissement si le code de l'API est plus récent) et la commande propose de
le régénérer ; sinon il est généré. Elle demande ensuite quels exemples importer :
synthétiques seuls, extrait DB existant de `build/microcks/`, ou nouvel extrait
(`make microcks-samples`). Sans terminal interactif : contrat régénéré, extrait DB importé
s'il existe. Cet export
reprend les schémas de l'application et ajoute des exemples synthétiques nommés pour `/health`
et les sept collections : aucune donnée réelle, aucun secret, aucune connexion à la DB.
Les collections simulées sont volontairement vides. `make openapi` permet de produire le
fichier seul ; `build/` est ignoré par Git.

### Exemples réels pour quelques dossiers

```sh
make microcks-samples   # lit la DB de .env en lecture seule, écrit build/microcks/
make microcks-import    # importe le contrat puis chaque build/microcks/examples-*.yaml
```

`scripts/export_microcks_samples.py` passe par les adaptateurs de l'API pour les dossiers de
`DOSSIER_UIDS` et produit des artefacts secondaires Microcks `APIExamples` (~13 fichiers,
~30 Mo). Le contrat OpenAPI reste synthétique : les données réelles ne vont que dans
`build/microcks/`, ignoré par Git. Ne jamais les committer ni les publier.

Requêtes mockées (toute autre combinaison répond `400` dans Microcks) :

| Route | Exemples |
| --- | --- |
| `/dossiers/{uid}` | les dossiers de `DOSSIER_UIDS` |
| `/textes`, `/articles` | `?dossier_uid=…` (20 premiers) et `&limit=100&offset=0, 100…` |
| `/textes/{uid}`, `/articles/{uid}` | tous les textes et articles de ces dossiers |
| `/amendements` | `?dossier_uid=…&texte_uid=…`, éventuellement `&article_uid=…`, mêmes pages |
| `/amendements/{uid}` | tous les amendements de ces textes |

Seuls `limit` absent (20) ou `limit=100`
avec un `offset` multiple de 100 sont mockés.

Limites Microcks contournées : chaque fichier importé est analysé par SnakeYAML (3 145 728
caractères au plus), d'où le découpage à 2,5 M caractères et l'échappement des caractères
interdits en YAML ; la limite d'envoi est relevée à 10 Mo dans `docker-compose.yml`
(`SPRING_SERVLET_MULTIPART_*`). Un contrat unique avec toutes les données dépasserait aussi
la limite de 16 Mo d'un document MongoDB.

Dans Microcks, ouvrir l'API importée et utiliser l'URL de mock affichée pour l'opération.
Un appel à un mock ne contacte **pas** la vraie API et ne vérifie pas son authentification.

### Vérifier le contrat de la vraie API

Après `make docker-up` et `make microcks-import`, dans Microcks :

1. Sélectionner le service importé, puis **NEW TEST**.
2. Choisir le runner **OPEN_API_SCHEMA** et l'endpoint `http://api:8000`.
3. Ajouter l'en-tête global `Authorization: Bearer <valeur locale de API_PASSWORD>` dans
   les paramètres du test, sans mettre ce secret dans le contrat ou un fichier suivi.
4. Lancer le test. Les exemples de vivacité et de collections sont vérifiés contre la vraie
   API ; des collections réelles non vides sont valides puisque le runner contrôle le schéma,
   pas l'égalité avec l'exemple vide. La DB doit être accessible pour ces appels.

Depuis Microcks, `api` est le nom DNS du conteneur ; `localhost` désignerait Microcks lui-même.
Pour essayer les autres endpoints directement, utiliser `/docs` et son bouton **Authorize**.
Référence : <https://microcks.io/documentation/references/artifacts/openapi-conventions/>.

## Authentification et ressources

Toutes les routes `/api/v0` exigent `Authorization: Bearer <mot-de-passe>`.

Le secret partagé est comparé en temps constant, sans fournir d'identité individuelle.
`/health` est public et mesure seulement la vivacité, pas la disponibilité des données.
Utiliser un secret aléatoire, HTTPS hors développement et masquer Authorization dans les logs.
Ne jamais placer de secret dans une URL, un exemple réel ou un fichier suivi.
Le SSO et les autorisations individuelles restent prévus pour v1

`create_app(Settings(...))` permet d'isoler la configuration. Le lifespan ouvre la base
(`core/database.py`) dans un thread : connexion DuckDB en mémoire, secret S3 éventuel, puis
`ATTACH … (READ_ONLY)` de `DATA_PATH` et verrouillage de la configuration. Chaque requête
reçoit son propre curseur (`Db`), placé dans la base attachée et fermé après la réponse ; les
routes sont synchrones et tournent dans le pool de threads de FastAPI. Une erreur d'E/S
(fichier ou S3 indisponible) donne `503`. Sans `DATA_PATH`, les routes de données répondent
`503` ; `/health` reste disponible.

## Ressources disponibles

Toutes les routes ci-dessous sont des `GET`, préfixées par `/api/v0` et authentifiées.
Chaque collection accepte `limit` et `offset` ; chaque détail absent répond `404`.

Deux hiérarchies, du haut vers le bas : **dossier → texte → article → amendement** et
**organe → groupe politique → personne** (les types d'organes sont un référentiel à part).
Une liste se filtre par le niveau juste au-dessus (facultatif) ; les niveaux plus hauts sont
obligatoires (`422` s'ils manquent). Un filtre sans correspondance donne une collection vide.

| Liste | Obligatoires | Facultatifs | Détail |
| --- | --- | --- | --- |
| `/dossiers` | — | — | `/dossiers/{uid}` |
| `/textes` | — | `dossier_uid` | `/textes/{uid}` |
| `/articles` | `dossier_uid` | `texte_uid` | `/articles/{uid}` |
| `/amendements` | `dossier_uid`, `texte_uid` | `article_uid` | `/amendements/{uid}` |
| `/organes/types` | — | — | — |
| `/organes` | — | `type` | `/organes/{uid}` |
| `/groupes_politiques` | — | `organe_uid`, `current` | `/groupes_politiques/{uid}` |
| `/personnes` | `organe_uid` | `groupe_uid`, `current` | `/personnes/{uid}` |

- `uid` est l'identifiant source (`DLR…`, `PRJL…`, `AMAN…`, `PO…`), jamais l'id interne : le
  pipeline renumérote les id à chaque reconstruction. Personne : son slug. Article (sans
  identifiant source) : `<uid du texte>-<ordre_place>`.
- Chaque objet porte une référence courte de ses parents (`DossierRef`, `TexteRef`,
  `ArticleRef`, `OrganeRef`, `GroupePolitiqueRef`, `PersonneRef`). `GroupePolitique` étend
  `Organe` (sous-type, comme dans le modèle).
- Groupes et personnes d'un organe : `current=true` (défaut) ne garde que les mandats en
  cours ; `current=false`, les mandats dont les périodes dans l'organe et le groupe se
  chevauchent.
- Les champs nullable restent présents avec `null` ; dates ISO 8601. Schémas détaillés :
  `/docs` et `/openapi.json`.

## Recherche

`GET /api/v0/search` interroge Meilisearch via `/multi-search`, une requête par type demandé.
Le front ne contacte jamais Meilisearch : la clé reste côté serveur, seuls les champs ci-dessous
sont acceptés et l'API construit elle-même les filtres (valeurs échappées, pas d'injection).

| Paramètre | Obligatoire | Défaut | Effet |
| --- | --- | --- | --- |
| `q` | oui | — | Texte cherché, 3 à 500 caractères |
| `types` | non | les trois | `amendements`, `dossiers`, `articles` (répétable) |
| `legislature` | non | — | Filtre tous les types |
| `dossier_uid` | non | — | Filtre tous les types |
| `groupe_politique` | non | — | Liste, amendements seulement (`RN`, `LFI-NFP`…) |
| `outcome` | non | — | Liste de sorts, amendements seulement (`Rejeté`…) |
| `semantic_ratio` | non | `0.5` | Part sémantique de la recherche hybride, 0 à 1 |
| `page` | non | `1` | 1 à 1000 |
| `hits_per_page` | non | `20` | 1 à 100 |

Exemple : `/api/v0/search?q=retraites&types=amendements&legislature=17&groupe_politique=RN&groupe_politique=LFI-NFP&outcome=Rejeté`.

Réponse : `{results: [{type, hits, facets, page, hits_per_page, total_pages, total_hits}]}`,
un groupe par type dans l'ordre demandé. Facettes : `groupe_politique` et `sort` pour les
amendements. Extraits surlignés dans `hits[]._formatted`, entourés de `<mark>` : `dispositif`
et `expose` (amendements), `contenu` (articles), `titre` et `loi_titre` (dossiers).

- Les `hits` sont les documents Meilisearch bruts : tout champ indexé est exposé, avec les noms
  de l'index. Ne pas indexer de donnée personnelle non publiable.
- `_formatted` n'échappe pas le HTML du document : le front doit l'assainir avant affichage.
- Index (`amendements`, `dossiers`, `articles`), embedder (`default`) et attributs sont définis
  dans `app/search/adapter.py` et doivent correspondre aux index réels. Attributs filtrables
  attendus : `legislature` partout, `dossier_id` (amendements, articles), `id` (dossiers),
  `groupe_politique` et `sort` (amendements).
- Meilisearch non configuré, injoignable ou en erreur : `503`, sans détail de l'erreur source.

## Accès aux sources et modèles

Flux : routeur → adaptateur de la fonctionnalité → curseur DuckDB en lecture seule.
Chaque adaptateur écrit son SQL paramétré (`$nom`) et traduit les colonnes du modèle V3 en
champs publics ; les routeurs ne manipulent aucun nom de colonne. Les références vers un autre
niveau sont des `STRUCT` construits par l'adaptateur propriétaire de la table (`ref()`),
désérialisés directement par Pydantic. Les libellés viennent des macros du modèle
(`libelle_procedure`, `libelle_type_organe`, `famille_du_type`). Aucune date de naissance,
coordonnée ni donnée d'import n'est exposée.

## Conventions de réponse et de pagination

- JSON, noms `snake_case`. Un objet simple est retourné directement, sans enveloppe `data`.
- Une collection suit toujours `{items, limit, offset, has_more}` ; pas de total implicite.
- `limit=20`, entre 1 et 100 ; `offset=0`, entre 0 et 10000. Paramètres invalides : `422`.
- Ordre stable : dossiers du plus récent au plus ancien ; textes dans l'ordre de la navette ;
  articles dans l'ordre du document ; amendements par numéro d'ordre ; personnes par nom.
- Lire `limit + 1` lignes puis retirer la ligne de contrôle pour calculer `has_more`.
- Pour avancer : `offset + limit` tant que `has_more` est vrai, dans la borne autorisée.
  Une pagination profonde nécessitera des filtres ou un curseur, pas une hausse sans limite.
- L'ordre est déterministe, mais la pagination offset ne fige pas les données entre requêtes.
- Les colonnes d'entrepôt (`created_at`, `import_id`, `source_hash`) restent internes.

`app/schemas.py` ne contient que la pagination partagée ; les réponses métier sont définies
par fonctionnalité (`articles/schemas.py`, `dossiers/schemas.py`, etc.). Le modèle V3 décrit
le stockage, pas le contrat HTTP : ne pas créer un schéma API pour chaque table.

## Conventions d'erreur et évolution

Toutes les erreurs utilisent RFC 9457 et `Content-Type: application/problem+json` :
`{type, title, status, detail, instance}`. `type=about:blank` utilise le titre HTTP standard.
`instance` contient uniquement le chemin ; les erreurs ne renvoient ni saisie brute, ni SQL,
ni détails de connexion. Les erreurs de validation indiquent les champs à corriger.

| Code | Sens |
| --- | --- |
| 401 | Identifiants absents ou invalides ; en-tête `WWW-Authenticate: Bearer` |
| 404 | Route ou ressource individuelle introuvable ; pas une collection vide |
| 422 | Paramètres invalides |
| 500 | Erreur interne inattendue ; message générique |
| 501 | Fonctionnalité pas encore implémentée |
| 503 | Accès, DB ou Meilisearch non configuré, indisponible ou délai dépassé |

L'API reste en v0 : retrait des données fictives et nouveaux champs d'article sont des
changements de contrat. Fixer le contrat avant v1 ; ensuite versionner toute rupture et
annoncer une période de migration. Les futurs endpoints reprennent ce flux sans service ou
interface générique supplémentaire tant qu'il n'y a pas de logique qui le justifie.

## Tests et mocks

Les mocks restent sous `tests/`, pas dans les adaptateurs applicatifs. Les tests de données
(`test_legislatif.py`, `test_acteurs.py`) traversent les vrais routeurs et adaptateurs sur une
base DuckDB en mémoire : le vrai `DATA_MODEL_V3_DUCKDB.sql` (contraintes comprises) rempli
par `tests/seed.sql`, données synthétiques branchées par `monkeypatch`. Aucun test ne lit la
vraie base, Meilisearch ou Keycloak. La recherche remplace le client Meilisearch par un
`httpx.MockTransport` qui vérifie la requête `/multi-search` envoyée. Une fabrique
d'application et un lifespan complet isolent chaque test ; ne jamais charger le `.env` réel.
