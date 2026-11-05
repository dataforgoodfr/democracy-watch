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

## 3. Hiérarchie et filtres

Dossier → texte → article → amendement. Chaque niveau se filtre par les identifiants des
niveaux supérieurs. Un paramètre obligatoire absent donne `422`.

| Route | Obligatoires | Optionnels |
| --- | --- | --- |
| `/dossiers` | — | `limit`, `offset` |
| `/textes` | `dossier_uid` | `text_reference`, `limit`, `offset` |
| `/articles` | `dossier_uid` | `text_reference`, `limit`, `offset` |
| `/amendements` | `dossier_uid`, `text_reference` | `article_uid`, `limit`, `offset` |

`text_reference` est la référence du texte (ex. `PRJLANR5L17B2247`), lue dans le champ
`text_reference` d'un article ou d'une ligne de `/textes`. Il n'y a pas encore
d'objet « texte » autonome : `/textes` renvoie une ligne par article.

### Dossiers

```ts
// Liste
const { data } = await useFetch<Page<Dossier>>('/api/dw/dossiers', { query: { limit: 20 } })
// Détail
const { data: dossier } = await useFetch<Dossier>(`/api/dw/dossiers/${dossierUid}`)
```

Champs : `uid, source_uid, title, legislative_term, status, procedure, submitted_at,
adopted_at, assembly_url, senate_url, legifrance_url, law_number, law_title,
law_published_at, subject_uid, updated_at`.

### Textes d'un dossier

```ts
const { data } = await useFetch<Page<Text>>('/api/dw/textes', {
  query: { dossier_uid: dossierUid, text_reference: undefined },
})
```

Une ligne par article, triée par référence de texte puis position. Champs : `uid, text_reference,
number, label, content, position, chamber, legislative_term, dossier_uid, source_url`.
Pour lister les textes distincts d'un dossier, regrouper côté front sur `text_reference`.

### Articles

```ts
// Articles d'un texte d'un dossier
const { data } = await useFetch<Page<Article>>('/api/dw/articles', {
  query: { dossier_uid: dossierUid, text_reference: textReference },
})
// Détail
const { data: article } = await useFetch<Article>(`/api/dw/articles/${articleUid}`)
```

Champs : `uid, text_reference, number, label, content, position, chamber, legislative_term,
dossier_uid, source_url`.

### Amendements

```ts
// Amendements d'un texte, éventuellement d'un seul article
const { data } = await useFetch<Page<Amendement>>('/api/dw/amendements', {
  query: {
    dossier_uid: dossierUid,
    text_reference: textReference,
    article_uid: articleUid, // optionnel
  },
})
// Détail
const { data: amendement } = await useFetch<Amendement>(`/api/dw/amendements/${uid}`)
```

Avec `article_uid`, les amendements « APRÈS ART. … » / « AVANT ART. … » ne sont pas renvoyés :
ils créent un nouvel article et ne visent aucun article existant. Les textes du Sénat n'ont pas
encore d'articles : filtrer par `article_uid` n'y renvoie rien.

Champs : `uid, source_uid, number, chamber, legislative_term, targeted_article, body,
explanation, outcome, submitted_at, author, text_reference, dossier_uid, parliamentarian_uid,
group_reference, author_reference, paragraph, paragraph_number, order_number,
parent_amendement_uid, sitting_reference, joint_discussion_id, identical_discussion_id`.

## 4. Acteurs politiques

Collections paginées (`limit`, `offset`, aucun filtre) et détail par `uid` :

| Liste | Détail | Champs |
| --- | --- | --- |
| `/parlementaires` | `/parlementaires/{uid}` | `uid, slug, first_name, last_name, chamber, active, group_uid, constituency_uid, photo_url, website` |
| `/groupes_politiques` | `/groupes_politiques/{uid}` | `uid, slug, name, chamber, active, full_name, short_name, color, political_position, legislative_term, active_member_count` |
| `/declarations_hatvp` | `/declarations_hatvp/{uid}` | `uid, parliamentarian_uid, document_type, submitted_at, published_at, status, dossier_url` |

```ts
const { data } = await useFetch<Page<Parliamentarian>>('/api/dw/parlementaires')
const { data: groupe } = await useFetch<PoliticalGroup>(`/api/dw/groupes_politiques/${uid}`)
```

`uid` est la clé primaire, pas le `slug` : `/parlementaires/{slug}` répond `404`.

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
