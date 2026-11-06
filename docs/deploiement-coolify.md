# Déploiement de l'API sur Coolify (D4G)

Retour d'expérience du premier déploiement de l'API (`backend/api`) sur le Coolify de Data For
Good, en novembre 2026. URL : `https://dw-api.services.d4g.fr` (doc interactive sur `/docs`).

## Configuration de la ressource

| Champ Coolify | Valeur |
|---|---|
| Source | Public Repository, `dataforgoodfr/democracy-watch` |
| Branch | la branche à déployer (pas forcément `main`) |
| Build Pack | `Dockerfile` (à la racine du dépôt) |
| Ports Exposes | `8000` |
| Ports Mappings | **vide** (voir plus bas) |
| Domains | `https://dw-api.services.d4g.fr` |
| Healthcheck | chemin `/health`, port `8000` |
| Container Labels | labels Traefik D4G (voir plus bas) |

Variables d'environnement : `API_KEY`, `DATABASE_URL`, `MEILI_URL`
(`https://dw-meilisearch.services.d4g.fr`), `MEILI_KEY` (clé de recherche, pas la clé maître),
et si besoin `MEILI_INDEX`, `MEILI_EMBEDDER`.

## Ce qu'on a appris

### Coolify construit depuis GitHub, pas depuis le poste

Un *Redeploy* reconstruit l'image à partir de la branche **poussée** sur GitHub. Un changement
local non commité ou non poussé n'est pas déployé, même après un Redeploy. Vérifier avec
`git log origin/<branche>` avant de déployer.

### Le domaine : `*.services.d4g.fr` est déjà en place

Le DNS `*.services.d4g.fr` pointe déjà vers le serveur Coolify, avec un certificat joker
Let's Encrypt. Il suffit de choisir un nom `X.services.d4g.fr` (ici `dw-api`) ; l'URL
`…sslip.io` proposée par Coolify n'est pas utile. Le DNS joker résout n'importe quel nom :
vérifier dans Coolify que le nom n'est pas déjà pris.

### Les labels Traefik par défaut de Coolify ne marchent pas chez D4G

Symptôme : `404 page not found` (réponse de Traefik, pas de l'API) sur toutes les URL, alors
que le conteneur est sain. Cause : le Traefik de D4G utilise le point d'entrée `webtls` et le
réseau `d4g-internal`, que les labels générés par Coolify n'utilisent pas.

Remplacer les *Container Labels* par ceux de la doc D4G (changer le nom du routeur, l'hôte et
le port) :

```
traefik.enable=true
traefik.http.routers.dw-api.rule=Host(`dw-api.services.d4g.fr`)
traefik.http.routers.dw-api.entryPoints=webtls
traefik.http.routers.dw-api.tls=true
traefik.docker.network=d4g-internal
traefik.http.services.dw-api.loadbalancer.server.port=8000
```

Règle D4G : ne jamais publier de port sur l'hôte (pas de `5432:5432`), d'où *Ports Mappings*
vide. Les labels ne sont appliqués qu'à la création du conteneur : redéployer après les avoir
changés.

Lecture des erreurs : une `404 page not found` veut dire que Traefik n'a pas de règle pour ce
nom (labels) ; une `502` veut dire qu'il a la règle mais n'atteint pas le conteneur (port).

### Le health check décide si Traefik envoie du trafic

Traefik ignore un conteneur tant que son health check n'est pas `healthy`. `/health` renvoie
503 si Postgres ou Meilisearch ne répond pas : un service en panne rend donc toute l'API
injoignable. Le `Dockerfile` installe `curl`, nécessaire au health check dans le conteneur.

### Changer une variable d'environnement demande un redémarrage

Les variables sont injectées à la création du conteneur et lues au démarrage de l'API. Après
une modification : *Restart* (ou *Redeploy* en cas de doute).

### Postgres : se connecter ne veut pas dire pouvoir lire les tables

Symptôme : `/health` répond `postgres: available` mais les routes `/api/v0/dossiers`,
`/textes`, `/amendements` renvoient 500, même pour un identifiant inconnu. Cause : l'utilisateur
en lecture seule pouvait se connecter (`SELECT 1` passe) mais n'avait pas `SELECT` sur les
tables.

À faire exécuter par un administrateur de la base :

```sql
GRANT SELECT ON dossiers_legislatifs, textes_articles, amendements TO <ro_user>;
```

Si la synchro CLAIR supprime et recrée les tables, ce droit disparaît à chaque synchro. Il faut
alors une règle par défaut, exécutée par le compte qui crée les tables :

```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO <ro_user>;
```

Pour tester des identifiants avant de les mettre dans Coolify :

```bash
psql "$DATABASE_URL" -c 'select current_user, count(*) from amendements'
```

### Taille de l'image

L'image faisait 746 Mo à cause de dépendances du template jamais utilisées (pandas, matplotlib,
Jupyter…). Après leur suppression : 336 Mo. Les outils de dev (`--no-dev`) ne sont pas dans
l'image.

## Vérifier un déploiement

```bash
API_KEY=<la clé> tests/smoke_api.sh https://dw-api.services.d4g.fr
```

Le script vérifie `/health`, le refus d'une mauvaise clé (401) et chaque route. Un code `000`
veut dire que rien ne répond à l'adresse donnée.

## Clé d'API

Les routes `/api/v0/*` exigent l'en-tête `X-API-Key` égal à `API_KEY` ; sans `API_KEY`
définie, elles sont toutes refusées. `/health` et `/docs` restent ouverts. Générer une clé :

```bash
openssl rand -hex 32
```

Ne pas mettre la clé dans le code exécuté par le navigateur : passer par le serveur du front
(par exemple une route serveur Nuxt qui relaie vers l'API en ajoutant l'en-tête). L'API n'a pas
de CORS configuré, un front statique ne peut donc pas l'appeler directement depuis un autre
domaine.
