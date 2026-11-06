// Accès à l'API Democracy Watch (via le relais Nuxt /api/v0) et conversion vers les cartes.
// La recherche ne porte que sur les amendements : textes et articles en sont déduits.

/** Morceau de texte : `mark` = terme recherché, `del` / `ins` = modification proposée. */
export type Segment = { t: string; k?: 'mark' | 'del' | 'ins' }

export type Texte = { titre: string; procedure: string; etat: string; depot: string; amendements: number }
export type Article = { libelle: string; dossier: string; extrait: Segment[]; amendements: number }
export type Amendement = {
  uid: string
  numero: string
  sort: string
  auteur: string
  groupe: string
  couleur?: string
  cible: string
  texte: string
  modification: Segment[]
}

/** Groupes parlementaires : couleur (maquette) et libellé exact dans l'API (filtre groupe_libelle). */
export const GROUPES: Record<string, { couleur: string; libelle: string }> = {
  GDR: { couleur: '#c70f2e', libelle: 'Gauche Démocrate et Républicaine' },
  'LFI-NFP': { couleur: '#b5174f', libelle: 'La France insoumise - Nouveau Front Populaire' },
  ECOS: { couleur: '#24733b', libelle: 'Écologiste et Social' },
  SOC: { couleur: '#c42961', libelle: 'Socialistes et apparentés' },
  LIOT: { couleur: '#8f6300', libelle: 'Libertés, Indépendants, Outre-mer et Territoires' },
  DEM: { couleur: '#b25900', libelle: 'Les Démocrates' },
  EPR: { couleur: '#876b00', libelle: 'Ensemble pour la République' },
  HOR: { couleur: '#1a70a6', libelle: 'Horizons & Indépendants' },
  DR: { couleur: '#1c57b8', libelle: 'Droite Républicaine' },
  UDR: { couleur: '#2b2e7a', libelle: 'Union des droites pour la République' },
  RN: { couleur: '#0a295c', libelle: 'Rassemblement National' },
}

type AmendementApi = {
  uid_an: string
  numero: string
  texte_ref: string | null
  article: string | null
  sort: string | null
  auteur_nom: string | null
  groupe_libelle: string | null
  groupe_couleur: string | null
  dossier_titre: string | null
  _formatted?: { dispositif?: string }
}
type RechercheApi = {
  results: {
    amendements: {
      hits: AmendementApi[]
      total: number
      facets: Record<string, Record<string, number>>
      search_mode: 'hybrid' | 'keyword'
    }
  }
}
type DossierApi = { titre: string; procedure_libelle: string | null; etat: string | null; date_depot: string | null }
type ArticleApi = { numero: string; contenu: string | null }

/** Badge du sort d'un amendement selon la valeur de l'API ; les autres sorts ont un badge neutre. */
export const SORTS: Record<string, { libelle: string; icone: string; classes: string }> = {
  'A discuter': { libelle: 'À discuter', icone: 'en-discussion', classes: 'bg-statut-info-fond text-statut-info' },
  'En traitement': { libelle: 'En traitement', icone: 'en-discussion', classes: 'bg-statut-info-fond text-statut-info' },
  Rejeté: { libelle: 'Rejeté', icone: 'rejete', classes: 'bg-statut-erreur-fond text-statut-erreur' },
  Adopté: { libelle: 'Adopté', icone: 'adopte', classes: 'bg-statut-succes-fond text-statut-succes' },
}

/** Sigle d'un groupe (LFI-NFP…) à partir de son libellé dans l'API. */
export function sigleGroupe(libelle: string): string {
  return Object.entries(GROUPES).find(([, g]) => g.libelle === libelle)?.[0] ?? libelle
}

const ENTITES: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' }

function decoder(html: string): string {
  return html
    .replace(/<[^>]*>/g, '')
    .replace(/&(#x?[0-9a-f]+|\w+);/gi, (e, c: string) =>
      c[0] === '#'
        ? String.fromCodePoint(parseInt(c.slice(1).replace(/^x/i, ''), c[1]?.toLowerCase() === 'x' ? 16 : 10))
        : (ENTITES[c] ?? e),
    )
}

/**
 * HTML de l'AN surligné par Meilisearch → segments de texte brut.
 * Seules les balises <mark> sont gardées (comme surlignage) : pas de v-html, donc pas d'injection.
 */
export function htmlEnSegments(html: string): Segment[] {
  return html
    .split(/(<mark>[\s\S]*?<\/mark>)/)
    .filter(Boolean)
    .map((part) =>
      part.startsWith('<mark>') ? { t: decoder(part.slice(6, -7)), k: 'mark' as const } : { t: decoder(part) },
    )
    .filter((s) => s.t.trim())
}

/** HTML de l'AN (dispositif, exposé) → paragraphes de texte brut. */
export function htmlEnParagraphes(html: string): string[] {
  return html
    .split(/<\/p>|<br\s*\/?>/i)
    .map((p) => decoder(p).trim())
    .filter(Boolean)
}

/** Surligne dans un texte brut les mots de la recherche (3 lettres ou plus). */
export function surligner(texte: string, q: string): Segment[] {
  const mots = q.split(/\s+/).filter((m) => m.length >= 3).map((m) => m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  if (!mots.length) return [{ t: texte }]
  // split avec un groupe capturant : les correspondances sont aux indices impairs
  return texte
    .split(new RegExp(`(${mots.join('|')})`, 'i'))
    .map((t, i): Segment => (i % 2 ? { t, k: 'mark' } : { t }))
    .filter((s) => s.t)
}

const ETATS: Record<string, string> = { promulgue: 'Promulgué' }

function dateFr(iso: string | null): string {
  // Les dates CLAIR sont minuit heure de Paris exprimé en UTC (ex. 2024-10-31T23:00:00).
  return iso ? new Date(`${iso}Z`).toLocaleDateString('fr-FR', { dateStyle: 'long', timeZone: 'Europe/Paris' }) : ''
}

function versAmendement(a: AmendementApi): Amendement {
  return {
    uid: a.uid_an,
    numero: `n°${a.numero}`,
    sort: a.sort ?? '',
    auteur: a.auteur_nom ?? 'Auteur inconnu',
    groupe: a.groupe_libelle ?? '',
    couleur: a.groupe_couleur ?? undefined,
    cible: a.article ?? '',
    texte: a.dossier_titre ?? '',
    modification: htmlEnSegments(a._formatted?.dispositif ?? ''),
  }
}

/** 3 premières clés d'une facette, par nombre décroissant. */
const top3 = (facette: Record<string, number> = {}) => Object.entries(facette).sort((a, b) => b[1] - a[1]).slice(0, 3)

/**
 * Une recherche : amendements trouvés, puis les dossiers et articles qui en reçoivent le plus.
 * Les articles sont comptés sur les ECHANTILLON premiers amendements (la facette « article »
 * ne dit pas à quel texte appartient l'article).
 */
const ECHANTILLON = 50
/** Part de recherche sémantique demandée (0 = mots-clés seuls, 1 = sémantique seule). */
const SEMANTIQUE = 0.5

export async function rechercher(q: string, groupes: string[]) {
  const { results } = await $fetch<RechercheApi>('/api/v0/search', {
    query: {
      q,
      types: 'amendements',
      semantic_ratio: SEMANTIQUE,
      limit: ECHANTILLON,
      facets: ['dossier_uid', 'article'],
      groupe_libelle: groupes,
    },
  })
  const { hits, total, facets, search_mode } = results.amendements

  const textes = await Promise.all(
    top3(facets.dossier_uid).map(async ([uid, n]): Promise<Texte> => {
      const d = await $fetch<DossierApi>(`/api/v0/dossiers/${uid}`)
      return {
        titre: d.titre,
        procedure: d.procedure_libelle ?? '',
        etat: ETATS[d.etat ?? ''] ?? d.etat ?? '',
        depot: dateFr(d.date_depot),
        amendements: n,
      }
    }),
  )

  // Paires (dossier, article) les plus amendées dans l'échantillon. Par dossier et non par
  // texte, pour ne pas afficher deux fois « ART. 2 » d'un même dossier (une par lecture).
  const paires = new Map<string, { hit: AmendementApi; refs: Set<string>; n: number }>()
  for (const h of hits) {
    if (!h.texte_ref || !h.article) continue
    const cle = `${h.dossier_titre}|${h.article}`
    const p = paires.get(cle) ?? { hit: h, refs: new Set<string>(), n: 0 }
    p.refs.add(h.texte_ref)
    p.n++
    paires.set(cle, p)
  }
  const articles = await Promise.all(
    [...paires.values()]
      .sort((a, b) => b.n - a.n)
      .slice(0, 3)
      .map(async ({ hit, refs, n }): Promise<Article> => {
        // Contenu de l'article dans le premier texte qui l'a (l'API n'a pas tous les articles)
        const numero = hit.article!.replace(/^ART\.\s*/, '')
        let contenu: string | null | undefined
        for (const ref of refs) {
          const liste = await $fetch<ArticleApi[]>(`/api/v0/textes/${ref}/articles`).catch(() => [])
          contenu = liste.find((a) => a.numero === numero)?.contenu
          if (contenu) break
        }
        return {
          libelle: hit.article!,
          dossier: hit.dossier_titre ?? '',
          extrait: contenu ? surligner(contenu.slice(0, 400), q) : [],
          amendements: n,
        }
      }),
  )

  return {
    // Sans requête, l'API ne fait jamais de sémantique : ce n'est pas un repli.
    semantiqueIndisponible: Boolean(q.trim()) && search_mode === 'keyword',
    amendements: hits.slice(0, 3).map(versAmendement),
    textes,
    articles,
    totaux: {
      amendements: total,
      textes: Object.keys(facets.dossier_uid ?? {}).length,
      articles: Object.keys(facets.article ?? {}).length,
    },
  }
}

type FicheApi = {
  uid: string
  numero: string
  texte_ref: string | null
  article_vise: string | null
  alinea: string | null
  dispositif: string | null
  expose_sommaire: string | null
  auteur_libelle: string | null
  auteur_ref: string | null
  sort: string | null
  date_depot: string | null
}

/**
 * Fiche d'un amendement : /amendements/{uid}, complété par la recherche pour le nom du groupe,
 * sa couleur et le dossier (absents de /amendements). Les filtres texte + auteur + article
 * limitent la recherche à quelques dizaines d'amendements, parmi lesquels on retrouve le bon.
 */
export async function chargerAmendement(uid: string) {
  const a = await $fetch<FicheApi>(`/api/v0/amendements/${uid}`)
  const meta = a.texte_ref && a.auteur_ref && a.article_vise
    ? (
        await $fetch<RechercheApi>('/api/v0/search', {
          query: { texte_ref: a.texte_ref, auteur: a.auteur_ref, article: a.article_vise, limit: 100 },
        }).catch(() => null)
      )?.results.amendements.hits.find((h) => h.uid_an === uid)
    : undefined
  // auteur_libelle : « M. Dupont, Mme Martin, … » — le premier est l'auteur
  const signataires = (a.auteur_libelle ?? '').split(/,\s*/).filter(Boolean)
  return {
    numero: a.numero,
    cible: [a.article_vise, a.alinea && `alinéa ${a.alinea}`].filter(Boolean).join(', '),
    sort: a.sort ?? '',
    depot: dateFr(a.date_depot),
    auteur: meta?.auteur_nom ?? signataires[0] ?? 'Auteur inconnu',
    groupe: meta?.groupe_libelle ?? '',
    couleur: meta?.groupe_couleur ?? undefined,
    dossier: meta?.dossier_titre ?? '',
    cosignataires: signataires.slice(1),
    dispositif: htmlEnParagraphes(a.dispositif ?? ''),
    expose: htmlEnParagraphes(a.expose_sommaire ?? ''),
  }
}
