<script setup lang="ts">
// Page de résultats de recherche (maquette « V0 - recherche élargie »).
// Tout vient de /api/v0 via le relais Nuxt ; textes et articles sont déduits des amendements.
type Onglet = 'tout' | 'textes' | 'articles' | 'amendements'

// La recherche est dans l'URL (/?q=…) : lien partageable, bouton retour, barre des autres pages.
// Sans q, la page démarre vide et n'appelle pas l'API.
const route = useRoute()
const requete = computed(() => String(route.query.q ?? ''))
const saisie = ref(requete.value)
watch(requete, (q) => (saisie.value = q))
const onglet = ref<Onglet>('tout')
const groupes = ref<string[]>([])

const { data, error } = await useAsyncData(
  'recherche',
  () => (requete.value.trim() ? rechercher(requete.value, groupes.value) : Promise.resolve(null)),
  { watch: [requete, groupes] },
)
const totaux = computed(() => data.value?.totaux ?? { textes: 0, articles: 0, amendements: 0 })
const total = computed(() => totaux.value.textes + totaux.value.articles + totaux.value.amendements)
const onglets = computed<{ id: Onglet; libelle: string }[]>(() => [
  { id: 'tout', libelle: `Tout - ${total.value}` },
  { id: 'textes', libelle: `Textes de loi - ${totaux.value.textes}` },
  { id: 'articles', libelle: `Articles - ${totaux.value.articles}` },
  { id: 'amendements', libelle: `Amendements - ${totaux.value.amendements}` },
])
const visible = (o: Onglet) => onglet.value === 'tout' || onglet.value === o
</script>

<template>
  <div class="min-h-screen">
    <EnTete
      v-model="saisie"
      :avertissement="
        data?.semantiqueIndisponible
          ? 'Recherche sémantique indisponible : résultats par mots-clés uniquement.'
          : undefined
      "
      @rechercher="navigateTo({ query: { q: saisie } })"
    />
    <main v-if="!requete.trim()" class="mx-auto max-w-[1440px] px-16 pt-10 pb-16">
      <p class="text-base leading-6 text-texte-mention">
        Recherchez un sujet dans les textes de loi, leurs articles et les amendements déposés à l'Assemblée nationale.
      </p>
    </main>
    <main v-else class="mx-auto flex max-w-[1440px] flex-col gap-10 px-16 pt-10 pb-16">
      <div class="flex flex-col gap-6 py-4">
        <div class="flex flex-col gap-1.5">
          <h1 class="text-[32px] leading-10 font-bold text-texte-titre">
            {{ total }} résultats pour « {{ requete.toLowerCase() }} »
          </h1>
          <p class="text-sm leading-6 text-texte-mention">
            Dans les textes de loi, leurs articles et les amendements déposés - Assemblée nationale uniquement
          </p>
        </div>
        <nav class="flex gap-2" aria-label="Type de résultats">
          <button
            v-for="o in onglets"
            :key="o.id"
            type="button"
            class="flex items-center gap-1.5 rounded-full px-3 py-1 text-sm leading-6"
            :class="onglet === o.id ? 'bg-fond-action font-bold text-texte-inverse' : 'bg-fond-neutre text-texte-titre'"
            :aria-pressed="onglet === o.id"
            @click="onglet = o.id"
          >
            <img v-if="onglet === o.id" src="/icons/check.svg" alt="" width="14" height="14" />
            {{ o.libelle }}
          </button>
        </nav>
      </div>

      <div class="flex items-start gap-10 py-6">
        <FiltresRecherche v-model:groupes="groupes" />
        <div class="flex min-w-0 flex-1 flex-col gap-10">
          <p v-if="error" class="text-sm text-statut-erreur">L'API n'a pas répondu ({{ error.statusCode }}).</p>
          <SectionResultats
            v-if="visible('textes')"
            titre="Textes de loi"
            :total="totaux.textes"
            :lien-voir-tout="`Voir les ${totaux.textes} textes`"
          >
            <CarteTexte v-for="t in data?.textes" :key="t.titre" :texte="t" />
          </SectionResultats>
          <SectionResultats
            v-if="visible('articles')"
            titre="Articles"
            :total="totaux.articles"
            :lien-voir-tout="`Voir les ${totaux.articles} articles`"
          >
            <CarteArticle v-for="(a, i) in data?.articles" :key="i" :article="a" />
          </SectionResultats>
          <SectionResultats
            v-if="visible('amendements')"
            titre="Amendements"
            :total="totaux.amendements"
            :lien-voir-tout="`Voir les ${totaux.amendements} amendements`"
          >
            <CarteAmendement v-for="(a, i) in data?.amendements" :key="i" :amendement="a" />
          </SectionResultats>
        </div>
      </div>
    </main>
  </div>
</template>
