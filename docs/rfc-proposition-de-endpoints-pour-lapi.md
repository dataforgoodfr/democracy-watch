# RFC : Proposition d'endpoints pour l'API

Date de clôture : vendredi 23 octobre 2026

# Motivation

Il nous faut un petit serveur qui expose en JSON les données dont les pages du site
Democracy Watch ont besoin.

# Proposition de nommage des objets principaux

Hiérarchie : `Dossier → Textes → Articles → Amendements`.

* **Dossier** : dossier législatif (projet ou proposition de loi, et quelques autres
  sous-types à lister). C'est le sujet et son parcours dans le temps : un identifiant stable
  (`dossier_uid`) qui regroupe toutes les versions du texte.
  * Champs importants : à compléter.
* **Texte** : l'état du dossier à une étape donnée (texte déposé, texte de commission,
  1re lecture AN…). Une référence (`texte_ref`) par étape.
  * Champs importants : à compléter.
* **Article** : article d'un texte. Le nom et le numéro d'un article peuvent changer d'un
  texte à l'autre au sein du même dossier.
  * Champs importants : à compléter.
* **Amendement** : amendement déposé sur un article (ou directement sur le texte, par exemple
  pour en modifier le titre).
  * Champs importants : à compléter.
  * Sous-amendements : pas d'objet dédié, ce sont des amendements qui portent sur un autre
    amendement. À préciser.

À ne pas confondre avec le **texte en vigueur** (le droit applicable, disponible sur
Légifrance). On en aura probablement besoin à terme, découpé lui aussi en articles, pour
afficher le diff produit par un dossier. Hors périmètre de cette RFC.

Les **votes** sont aussi hors périmètre de cette v0.

C'est sur la distinction dossier / texte qu'on profite du travail de CLAIR.

# Implémentation proposée

Langage : Python

Bibliothèque : FastAPI

## Endpoints

| Méthode | Route | Rôle |
|---------|-------|------|
| GET     | `/api/v0/search` | Recherche générique : `q`, `types` (répétable : `amendements`, `dossiers`, `articles`), `mode=federated\|grouped`, `semantic_ratio`, filtres (`legislature`, `dossier_uid`, `texte_ref`…), `page`, `limit` |
| GET     | `/api/v0/dossiers/{dossier_uid}` | Fiche d'un dossier et la liste de ses textes |
| GET     | `/api/v0/textes/{texte_ref}/articles` | Liste des articles d'un texte |
| GET     | `/api/v0/amendements/{uid}` | Un amendement |
| GET     | `/health` | État de Postgres et de Meilisearch |

Les paramètres multivalués se passent en répétant le paramètre (`types=a&types=b`), ce que
FastAPI gère nativement avec `list[str]`.

### GET `/api/v0/search`

Appelle directement Meilisearch (`/multi-search`), une requête par index demandé.

* `types` : index dans lesquels chercher.
* `semantic_ratio` : proportion entre recherche sémantique et recherche textuelle (0 = texte
  seul, 1 = sémantique seule). Ne s'applique qu'aux index qui ont un embedder ; les autres
  sont interrogés en recherche textuelle.
* `mode` :
  * `grouped` : un tableau de résultats par index (un d'amendements, un de dossiers…), chacun
    paginé et facetté séparément ;
  * `federated` : tous les résultats dans un seul tableau classé par pertinence, paginé
    globalement.
* Filtres : chaque filtre ne s'applique qu'aux index qui ont l'attribut (par exemple
  `groupe_politique` et `sort_amendement` n'existent que pour les amendements). Le serveur
  tient la correspondance filtre → index, car Meilisearch renvoie une erreur sur un attribut
  non filtrable.
* `sort_amendement` : issue de l'amendement (`Adopté`, `Rejeté`…). Nommé ainsi pour ne pas
  le confondre avec le tri, qui se fait via `order`.
* Surlignage : les champs `dispositif` et `expose` contiennent du HTML issu de l'AN. Le
  serveur doit assainir le HTML renvoyé par Meilisearch (en ne gardant que `<mark>` et les
  balises de mise en forme attendues) avant que le front l'injecte dans la page.
* `search_mode` (dans la réponse, par type) : `hybrid` si la recherche sémantique a été
  demandée et a fonctionné, `keyword` sinon. Si le service d'embedding ne répond pas, le
  serveur relance la recherche en mots-clés seuls et renvoie quand même un 200, avec
  `search_mode: "keyword"` : le front peut s'en servir pour signaler que la recherche
  sémantique est indisponible. Attention : `hybrid` ne garantit pas que des résultats
  viennent de la sémantique, car Meilisearch saute la partie sémantique quand les mots-clés
  suffisent à remplir la page.

Exemple :

```http
GET /api/v0/search
  ?q=retraites
  &types=amendements&types=dossiers
  &mode=grouped
  &semantic_ratio=0.5
  &legislature=17
  &dossier_uid=DLR5L17N12345
  &groupe_politique=RN&groupe_politique=LFI-NFP
  &sort_amendement=Adopté&sort_amendement=Rejeté
  &date_min=2025-01-01&date_max=2025-06-30
  &facets=groupe_politique&facets=sort_amendement
  &order=date_depot:desc
  &page=1&limit=20
```

Côté serveur, la requête envoyée à Meilisearch en mode `grouped` (pagination et facettes par
requête) :

```python
queries = [
    {
        "indexUid": INDEXES["amendements"],
        "q": "retraites",
        # Tableau extérieur = ET, sous-tableau = OU
        "filter": [
            "legislature = 17",
            any_of("groupe_politique", ["RN", "LFI-NFP"]),
            any_of("sort", ["Adopté", "Rejeté"]),
        ],
        "facets": ["groupe_politique", "sort"],
        "sort": ["date_depot:desc"],
        "hybrid": {"embedder": EMBEDDER, "semanticRatio": 0.5},
        "attributesToHighlight": ["dispositif", "expose"],
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
        "page": 1,
        "hitsPerPage": 20,
    },
    # … une requête par index de `types`
]

res = client.multi_search(queries)
```

En mode `federated`, Meilisearch refuse la pagination et les facettes dans chaque requête :
elles passent au niveau `federation`.

```json
POST /multi-search
{
  "federation": {
    "limit": 20,
    "offset": 0,
    "facetsByIndex": { "amendements-2": ["groupe_politique", "sort"] }
  },
  "queries": [
    { "indexUid": "dossiers", "q": "retraites", "federationOptions": { "weight": 1.5 } },
    {
      "indexUid": "amendements-2",
      "q": "retraites",
      "filter": ["legislature = 17"],
      "hybrid": { "embedder": "hf-t4", "semanticRatio": 0.5 }
    }
  ]
}
```

Le paramètre `sort_amendement` de l'API correspond à l'attribut `sort` de l'index
Meilisearch.
