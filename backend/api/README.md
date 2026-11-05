# Democracy Watch API

Guide pas à pas (installation, `.env`, lancement, tests) : [LOCAL_DEV.md](../../LOCAL_DEV.md).

## Démarrage (depuis la racine du dépôt)

- Installer : `uv sync`.
- Définir `API_PASSWORD` et `DATABASE_URL` dans l'environnement ou le `.env` local non suivi.
  `DATABASE_URL` accepte `postgresql://...` ou `postgresql+asyncpg://...`, sans variables non
  résolues ; utiliser un rôle SQL en lecture seule.
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
- `make check-connections` vérifie, en lecture seule, l'accès à Postgres (`SELECT 1`) et à
  Meilisearch (`/health`, puis `/version` pour valider la clé) configurés dans `.env`.
- `make health`, `make docker-logs`, `make docker-check` et `make docker-down` permettent
  de vérifier la vivacité, suivre les logs, valider Compose sans afficher les secrets et arrêter
  les conteneurs sans supprimer les volumes. `make help` liste les commandes.
- L'API utilise la DB de `DATABASE_URL` dans le `.env` racine. Postgres local et Keycloak
  restent optionnels, sous les profils Compose `local-db` et `sso` ; ils ne sont pas démarrés
  par défaut et le Postgres local ne contient pas le dump partagé.
- Le service `meilisearch` (v1.15.2, port `127.0.0.1:7700`, volume `meili_data`) démarre avec
  `docker-up` ; l'API le joint sur `http://meilisearch:7700`. Il démarre vide : la recherche
  répond `503` tant que les index et l'embedder ne sont pas créés.

### Essayer des mocks sans accéder à Postgres

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

### Exemples réels pour neuf dossiers

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
| `/dossiers/{dossier_uid}` | les 9 dossiers |
| `/textes`, `/articles` | `?dossier_uid=…` (20 premiers) et `&limit=100&offset=0, 100…` |
| `/articles/{uid}` | tous les articles de ces dossiers |
| `/amendements` | `?dossier_uid=…&text_reference=…`, éventuellement `&article_uid=…`, mêmes pages |
| `/amendements/{uid}` | les amendements des textes ayant des articles |

Les amendements d'un dossier portant sur un texte absent de `textes_articles` ne sont pas
exportés (aucun `text_reference` ne les atteint). Seuls `limit` absent (20) ou `limit=100`
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
`/health` est public et mesure seulement la vivacité, pas la disponibilité de Postgres.
Utiliser un secret aléatoire, HTTPS hors développement et masquer Authorization dans les logs.
Ne jamais placer de secret dans une URL, un exemple réel ou un fichier suivi.
Le SSO et les autorisations individuelles restent prévus pour v1

`create_app(Settings(...))` permet d'isoler la configuration. Le lifespan crée le moteur sans
connexion à l'import et le ferme même après un démarrage partiellement échoué. La fermeture
est protégée de l'annulation par une portée AnyIO (socle d'Asyncer). Les sessions
sont ouvertes et fermées par requête ; aucune route n'écrit dans les sources.
Sans `DATABASE_URL`, les routes qui exigent la DB répondent `503` ; `/health` reste disponible.

Les connexions sont créées directement par `asyncpg` via `democracy_watch.db.connect_async`.
SQLAlchemy conserve la gestion du pool et l'exécution des projections des adaptateurs, sans
recevoir les identifiants dans son URL de moteur. Le helper est aussi réutilisable hors API :
`await connect_async()` utilise `DATABASE_URL` ou les variables `PG*` de l'environnement ;
l'appelant doit fermer la connexion avec `await connection.close()`. Il ne charge pas `.env`.

Le pool est borné à `DATABASE_POOL_SIZE` connexions (5 par défaut, sans débordement).
`DATABASE_POOL_TIMEOUT` borne l'attente du pool (10 secondes par défaut) ; `DATABASE_TIMEOUT`
borne connexion, commande et requête SQL (10 secondes). Les transactions sont en lecture seule.
Prévoir au maximum `workers × réplicas × DATABASE_POOL_SIZE` connexions et un rôle SQL restreint.
Les appels SQLAlchemy sont directement attendus ; aucun appel direct aux primitives asyncio.
Pour de futurs traitements synchrones bloquants, utiliser `asyncer.asyncify`, pas le thread
événementiel. Inutile d'envelopper des opérations déjà asynchrones.

## Ressources disponibles

Toutes les routes ci-dessous sont des `GET`, préfixées par `/api/v0` et authentifiées.
Chaque collection accepte `limit` et `offset` ; chaque détail absent répond `404`.

| Collection | Détail | Principales informations exposées |
| --- | --- | --- |
| `/amendements` | `/amendements/{uid}` | Numéro, chambre, législature, article visé, alinéa, dispositif, exposé, sort, dépôt, auteur, groupe, références, amendement parent, séance et discussions commune/identique |
| `/dossiers` | `/dossiers/{dossier_uid}` | Titre, législature, état, procédure, dépôt/adoption, liens AN/Sénat/Légifrance, loi (numéro, titre, date JO), sujet, mise à jour |
| `/textes` | — | Une ligne par article du dossier : référence du texte, numéro, libellé, contenu, position, chambre, législature, dossier et source |
| `/articles` | `/articles/{uid}` | Référence du texte, numéro, libellé, contenu, position, chambre, législature, dossier et source |
| `/parlementaires` | `/parlementaires/{uid}` | Nom, prénom, slug, chambre, activité, groupe, circonscription, photo et site |
| `/groupes_politiques` | `/groupes_politiques/{uid}` | Noms, slug, chambre, activité, couleur, position politique, législature et effectif actif |
| `/declarations_hatvp` | `/declarations_hatvp/{uid}` | Parlementaire, type de document, dates, statut et lien du dossier ; pas de XML brut |

`uid` désigne toujours la **clé primaire de la base**, pas un slug. Les relations `*_uid`
utilisent ces mêmes identifiants. Les amendements et dossiers exposent en plus `source_uid`
pour leur identifiant externe CLAIR, distinct de la clé primaire : utiliser `uid` dans l'URL.
Les champs nullable restent explicitement présents avec `null` ; les dates sont sérialisées
au format ISO 8601. Les schémas détaillés sont visibles dans `/docs` et `/openapi.json`.

### Filtres hiérarchiques

Hiérarchie : dossier → texte → article → amendement. Chaque collection se filtre par les
identifiants des niveaux supérieurs ; un paramètre obligatoire absent donne `422`.

| Collection | Obligatoires | Optionnels |
| --- | --- | --- |
| `/dossiers` | — | `limit`, `offset` |
| `/textes` | `dossier_uid` | `text_reference`, `limit`, `offset` |
| `/articles` | `dossier_uid` | `text_reference`, `limit`, `offset` |
| `/amendements` | `dossier_uid`, `text_reference` | `article_uid`, `limit`, `offset` |

`text_reference` est la référence CLAIR du texte (`texte_ref`, ex. `PRJLANR5L17B2247`).
Le mapping fourni décrit `textes_articles`, pas une table autonome de textes : `/textes`
renvoie donc une ligne par article, sans regroupement ni titre inventé. Un filtre sans
correspondance donne une collection vide avec `200`.

Aucune clé ne relie un amendement à un article : `article_uid` retrouve l'article puis garde
les amendements du même texte dont `article_vise`, sans préfixe `ART.`/`Article` et en
majuscules, égale le `numero` de l'article (`ART. 14` → `14`, `ART. PREMIER` → `PREMIER`).
Les amendements `APRÈS ART. …`/`AVANT ART. …` créent un article et ne sont donc rattachés
à aucun article existant. `textes_articles` ne contient pas de texte du Sénat.

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

Flux : routeur → adaptateur de la fonctionnalité → session Postgres en lecture seule.
Les adaptateurs utilisent les modèles générés de `backend/schemas/database_mapping.py`
pour construire des projections SQL paramétrées, sans chargement implicite des relations ORM.
Le mapping a été déplacé sans modifier ses définitions. Docker et le script de génération
référencent le nouveau chemin ; aucun import applicatif ne dépend du répertoire `scripts`.
Les adaptateurs traduisent les noms CLAIR en champs publics ; les routeurs ne manipulent pas
les noms de colonnes source. Aucun JSON source, XML HATVP, date de naissance ou email n'est
exposé automatiquement.

## Conventions de réponse et de pagination

- JSON, noms `snake_case`. Un objet simple est retourné directement, sans enveloppe `data`.
- Une collection suit toujours `{items, limit, offset, has_more}` ; pas de total implicite.
- `limit=20`, entre 1 et 100 ; `offset=0`, entre 0 et 10000. Paramètres invalides : `422`.
- Ordre stable : clé primaire pour les objets ; textes par référence, position puis
  identifiant ; les articles sont
  ordonnés par référence puis position et identifiant (position/identifiant si filtrés).
- Lire `limit + 1` lignes puis retirer la ligne de contrôle pour calculer `has_more`.
- Pour avancer : `offset + limit` tant que `has_more` est vrai, dans la borne autorisée.
  Une pagination profonde nécessitera des filtres ou un curseur, pas une hausse sans limite.
- L'ordre est déterministe, mais la pagination offset ne fige pas les données entre requêtes.
- Article public : `{uid, text_reference, number, label, content, position, chamber,
  legislative_term, dossier_uid, source_url}`. Les dates techniques restent internes.

`app/schemas.py` ne contient que la pagination partagée ; les réponses métier sont définies
par fonctionnalité (`articles/schemas.py`, `dossiers/schemas.py`, etc.). Les modèles SQLAlchemy générés décrivent le stockage,
pas le contrat HTTP : ne pas créer un schéma API pour chaque table ni les exposer directement.
Ne pas modifier les modèles générés pour satisfaire une réponse HTTP.

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

Les mocks restent sous `tests/`, pas dans les adaptateurs applicatifs. Le test d'articles
traverse le vrai routeur et le vrai adaptateur avec une session simulée : SQL paramétré,
ordre, mapping, pagination, validation, authentification et pannes DB sont vérifiés sans
contacter Postgres, Meilisearch ou Keycloak. La recherche remplace le client Meilisearch par un
`httpx.MockTransport` qui vérifie la requête `/multi-search` envoyée. Une fabrique d'application et un lifespan complet
isolent chaque test ; ne jamais charger le `.env` réel pour les tests.
