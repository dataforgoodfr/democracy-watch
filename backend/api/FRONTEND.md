# Appeler l'API depuis Nuxt (`useFetch`)

Guide pour l'équipe front. Le contrat complet (types, champs, erreurs) est généré par l'API :
`/docs` (Swagger) et `/openapi.json`. En cas de doute, ces deux pages font foi.

## 1. Ne jamais appeler l'API directement depuis le navigateur

Toutes les routes `/api/v0` exigent `Authorization: Bearer <API_PASSWORD>`. Ce mot de passe
est **partagé** : s'il est placé dans `runtimeConfig.public`, dans le bundle ou dans un appel
fait par le navigateur, tout visiteur peut le lire et l'utiliser.

Passer par une route serveur Nuxt (Nitro) qui ajoute l'en-tête côté serveur :

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // Privé (serveur uniquement) : NUXT_DW_API_URL et NUXT_DW_API_PASSWORD
    dwApiUrl: 'http://127.0.0.1:8000',
    dwApiPassword: '',
  },
})
```

```ts
// server/api/dw/[...path].ts
export default defineEventHandler((event) => {
  // L'API est en lecture seule : refuser tout autre verbe.
  assertMethod(event, 'GET')
  const { dwApiUrl, dwApiPassword } = useRuntimeConfig(event)
  const path = getRouterParam(event, 'path')
  const { search } = getRequestURL(event)
  return proxyRequest(event, `${dwApiUrl}/api/v0/${path}${search}`, {
    headers: { Authorization: `Bearer ${dwApiPassword}` },
  })
})
```

Dans les composants, appeler ensuite `/api/dw/...` :

```ts
const { data, error, status } = await useFetch('/api/dw/dossiers')
```

Les exemples ci-dessous supposent ce proxy.

## 2. Conventions communes

- Toutes les routes sont des `GET`, réponses JSON en `snake_case`.
- `uid` est toujours la clé primaire de la base : c'est lui qu'on met dans les URL et les
  filtres (`dossier_uid`, `article_uid`…). `source_uid` est l'identifiant externe CLAIR, à
  afficher éventuellement mais pas à réutiliser dans les appels.
- Les champs nullable sont toujours présents (`null`) ; les dates sont en ISO 8601.
- Passer les paramètres via `query` : `useFetch` les encode et recharge automatiquement
  quand une valeur réactive change. Les tableaux deviennent des clés répétées
  (`types=amendements&types=dossiers`), format attendu par l'API.
- Un paramètre `undefined` n'est pas envoyé : pratique pour les filtres optionnels.

### Pagination des collections

```ts
type Page<T> = { items: T[]; limit: number; offset: number; has_more: boolean }
```

- `limit` : 1 à 100 (défaut 20). `offset` : 0 à 10000 (défaut 0).
- Page suivante : `offset + limit` tant que `has_more` est vrai. Pas de total.

```ts
const offset = ref(0)
const { data } = await useFetch<Page<Dossier>>('/api/dw/dossiers', {
  query: { limit: 20, offset },
})
const next = () => { if (data.value?.has_more) offset.value += 20 }
```

### Erreurs

Format RFC 9457 (`application/problem+json`) :

```ts
type Problem = { type: string; title: string; status: number; detail: string; instance: string }
```

| Code | Quand | Côté front |
| --- | --- | --- |
| 401 | Mot de passe absent ou faux | Problème de config du proxy, pas de l'utilisateur |
| 404 | Détail introuvable (une collection vide reste `200`) | Afficher « introuvable » |
| 422 | Paramètre manquant ou invalide ; `detail` liste les champs | Bug d'appel à corriger |
| 503 | Base ou moteur de recherche indisponible | Message « réessayez plus tard » |

```ts
const { data, error } = await useFetch('/api/dw/dossiers/inconnu')
if (error.value?.statusCode === 404) { /* introuvable */ }
// Corps Problem : error.value?.data?.detail
```

## 3. Hiérarchies et filtres

Deux hiérarchies, du haut vers le bas :

- travail législatif : dossier → texte → article → amendement ;
- acteurs : organe → groupe politique → personne (types d'organes à part, `/organes/types`).

Règle de filtrage d'une liste : le niveau **juste au-dessus** est facultatif, les niveaux
plus hauts sont obligatoires (`422` s'ils manquent). Un objet seul se lit par son `uid`.
Filtre sans correspondance (ex. texte d'un autre dossier) : collection vide, `200`.

| Liste | Obligatoires | Facultatifs | Détail |
| --- | --- | --- | --- |
| `/dossiers` | — | — | `/dossiers/{uid}` |
| `/textes` | — | `dossier_uid` | `/textes/{uid}` |
| `/articles` | `dossier_uid` | `texte_uid` | `/articles/{uid}` |
| `/amendements` | `dossier_uid`, `texte_uid` | `article_uid` | `/amendements/{uid}` |
| `/organes` | — | `type` | `/organes/{uid}` |
| `/groupes_politiques` | — | `organe_uid`, `current` | `/groupes_politiques/{uid}` |
| `/personnes` | `organe_uid` | `groupe_uid`, `current` | `/personnes/{uid}` |

Toutes les listes acceptent aussi `limit` et `offset`.

`uid` est l'identifiant source, stable d'un chargement à l'autre : `DLR5L17N50879` (dossier),
`PIONANR5L17BTC0699` (texte), `AMANR5L17PO838901BTC0699P0D1N000001` (amendement), `PO838901`
(organe, groupe), slug pour une personne (`marie-dupont`). Un article n'a pas d'identifiant
source : son `uid` vaut `<uid du texte>-<position>` (ex. `PIONANR5L17BTC0699-15`).

Chaque objet embarque une référence courte (`*Ref`) de ses parents : un amendement porte
`dossier`, `texte`, `article`, `author`, `groupe`… sans appel supplémentaire.

### Travail législatif

```ts
const { data: dossiers } = await useFetch<Page<Dossier>>('/api/dw/dossiers')
const { data: textes } = await useFetch<Page<Texte>>('/api/dw/textes', {
  query: { dossier_uid: dossierUid },
})
const { data: articles } = await useFetch<Page<Article>>('/api/dw/articles', {
  query: { dossier_uid: dossierUid, texte_uid: texteUid /* facultatif */ },
})
const { data: amendements } = await useFetch<Page<Amendement>>('/api/dw/amendements', {
  query: { dossier_uid: dossierUid, texte_uid: texteUid, article_uid: articleUid /* facultatif */ },
})
```

| Objet | Champs |
| --- | --- |
| `Dossier` | `uid, title, short_title, procedure, procedure_label, status, outcome, submitted_on, outcome_on, loi` (`loi` : dossier promulgué seulement) |
| `Texte` | `uid, nature, number, dossier, chamber, term, position, title, submitted_on` |
| `Article` | `uid, number, label, texte, dossier, position, is_placeholder, is_deleted, content` |
| `Amendement` | `uid, number, dossier, texte, article, targeted_article, paragraph_number, parent_uid, examining_organe, author, author_organe, groupe, status, outcome, outcome_reason, submitted_on, outcome_at, body, explanation` |

Un article « emplacement » (`is_placeholder`, `number` à `null`) est le titre ou l'intervalle
entre deux articles (« Après l'article 2 ») : c'est là que pointent les amendements qui
créent un article. `article` d'un amendement est `null` si l'emplacement visé n'est pas
résolu ; `targeted_article` garde alors le libellé source.

## 4. Acteurs politiques

```ts
const { data: types } = await useFetch<TypeOrgane[]>('/api/dw/organes/types')
const { data: commissions } = await useFetch<Page<Organe>>('/api/dw/organes', {
  query: { type: 'COMPER' },
})
// Groupes représentés à l'Assemblée de la XVIIe législature
const { data: groupes } = await useFetch<Page<GroupePolitique>>('/api/dw/groupes_politiques', {
  query: { organe_uid: 'PO838901' },
})
// Députés RN de la XVIIe législature
const { data: deputes } = await useFetch<Page<Personne>>('/api/dw/personnes', {
  query: { organe_uid: 'PO838901', groupe_uid: 'PO845401' },
})
```

| Objet | Champs |
| --- | --- |
| `TypeOrgane` | `code, label, family, chamber` |
| `Organe` | `uid, type, name, short_name, type_label, family, chamber, parent_uid, start_date, end_date` |
| `GroupePolitique` | champs d'`Organe` + `color, logo_url, political_position` |
| `Personne` | `uid, first_name, last_name, civility, profession, photo_url, groupe` (groupe actuel) |

`current=true` (défaut) : seuls les mandats en cours comptent. `current=false` : tout mandat
passé, à condition que les périodes dans l'organe et dans le groupe se chevauchent.

## 5. Recherche

```ts
const q = ref('retraites')
const groupes = ref<string[]>(['RN', 'LFI-NFP'])
const page = ref(1)

const { data } = await useFetch<SearchResults>('/api/dw/search', {
  query: {
    q,                              // obligatoire, 3 à 500 caractères
    types: ['amendements'],         // défaut : amendements, dossiers, articles
    legislature: 17,                // filtre tous les types
    dossier_uid: undefined,         // filtre tous les types
    groupe_politique: groupes,      // amendements seulement
    outcome: ['Rejeté'],            // sort de l'amendement, amendements seulement
    semantic_ratio: 0.5,            // 0 = mots-clés, 1 = sémantique
    page,                           // 1 à 1000
    hits_per_page: 20,              // 1 à 100
  },
  // Éviter un appel (et un 422) tant que la saisie est trop courte.
  immediate: q.value.length >= 3,
})
```

Réponse, un groupe par type demandé :

```ts
type SearchGroup = {
  type: 'amendements' | 'dossiers' | 'articles'
  hits: Record<string, unknown>[]      // documents de l'index, noms de champs de l'index
  facets: Record<string, Record<string, number>> // ex. { groupe_politique: { RN: 12 } }
  page: number
  hits_per_page: number
  total_pages: number
  total_hits: number
}
type SearchResults = { results: SearchGroup[] }
```

- Contrairement aux collections, la recherche pagine par `page` et donne des totaux.
- Facettes disponibles : `groupe_politique` et `sort` (amendements) ; à utiliser pour afficher
  les compteurs des filtres.
- Extraits surlignés dans `hit._formatted`, entourés de `<mark>…</mark>` : `dispositif`,
  `expose` (amendements), `contenu` (articles), `titre`, `loi_titre` (dossiers).
- **Sécurité :** `_formatted` n'échappe pas le HTML du document. Ne pas le passer tel quel à
  `v-html` : l'assainir d'abord (ex. DOMPurify en n'autorisant que `<mark>`).
- Pour une saisie au clavier, temporiser (`refDebounced` de VueUse) avant de mettre à jour `q`.
- `503` : moteur de recherche indisponible ou index pas encore créés.

## 6. Types TypeScript

Plutôt que de recopier les types, les générer depuis le contrat :

```sh
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o types/dw-api.d.ts
```

Regénérer après chaque changement d'API : la v0 peut encore évoluer.
