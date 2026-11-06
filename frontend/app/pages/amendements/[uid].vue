<script setup lang="ts">
import { sigleGroupe } from '~/utils/api'

// Fiche d'un amendement (structure de la maquette « Fiche amendement », styles V0).
// Seuls les blocs que l'API sait remplir sont affichés : dispositif, exposé, signataires.
const route = useRoute()
const uid = String(route.params.uid)
const saisie = ref('')

const { data: a, error } = await useAsyncData(`amendement-${uid}`, () => chargerAmendement(uid))
// Retour aux résultats ; ouverte directement (lien partagé), la fiche renvoie à l'accueil.
const router = useRouter()
const retour = () => (window.history.state?.back ? router.back() : navigateTo('/'))
useHead({ title: () => (a.value ? `Amendement n° ${a.value.numero} - Democracy Watch` : 'Democracy Watch') })
</script>

<template>
  <div class="min-h-screen">
    <EnTete v-model="saisie" @rechercher="navigateTo({ path: '/', query: { q: saisie } })" />
    <main class="mx-auto flex max-w-[1440px] flex-col gap-8 px-16 pt-10 pb-16">
      <p v-if="error" class="text-sm text-statut-erreur">
        {{ error.statusCode === 404 ? 'Amendement introuvable.' : `L'API n'a pas répondu (${error.statusCode}).` }}
      </p>
      <template v-else-if="a">
        <div class="flex flex-col gap-3">
          <button type="button" class="self-start text-sm leading-6 text-texte-mention underline" @click="retour">
            ← Retour aux résultats
          </button>
          <div class="flex flex-wrap items-baseline gap-x-3">
            <h1 class="text-[32px] leading-10 font-bold text-texte-titre">Amendement n° {{ a.numero }}</h1>
            <span class="text-base leading-6 text-texte-mention">{{ a.cible }}</span>
          </div>
          <p class="flex flex-wrap items-center gap-2 text-sm leading-6">
            <span class="size-2 rounded-full" :style="{ backgroundColor: a.couleur }" />
            <strong :style="{ color: a.couleur }">
              {{ a.auteur }}<template v-if="a.groupe"> ({{ sigleGroupe(a.groupe) }})</template>
            </strong>
            <span v-if="a.cosignataires.length" class="text-texte-mention">+{{ a.cosignataires.length }} cosignataires</span>
            <span v-if="a.depot" class="text-texte-mention">- Déposé le {{ a.depot }}</span>
          </p>
          <div class="flex flex-wrap gap-2">
            <BadgeSort :sort="a.sort" />
            <span v-if="a.dossier" class="badge bg-fond-selection text-texte-titre">{{ a.dossier }}</span>
          </div>
        </div>

        <div class="flex items-start gap-10">
          <div class="flex min-w-0 flex-1 flex-col gap-6">
            <section class="flex flex-col gap-3 rounded-lg border border-bordure-defaut bg-fond-surface p-6">
              <h2 class="badge self-start bg-transparent px-0 text-texte-mention">Texte exact - dispositif</h2>
              <p v-for="(p, i) in a.dispositif" :key="i" class="font-loi text-base leading-7 text-texte-defaut">{{ p }}</p>
            </section>
            <section
              v-if="a.expose.length"
              class="flex flex-col gap-3 rounded-lg border border-bordure-defaut bg-fond-surface p-6"
            >
              <h2 class="badge self-start bg-transparent px-0 text-texte-mention">Exposé sommaire - ce que l'auteur dit</h2>
              <p v-for="(p, i) in a.expose" :key="i" class="text-sm leading-6 text-texte-defaut">{{ p }}</p>
            </section>
          </div>

          <aside class="flex w-[338px] shrink-0 flex-col gap-4 rounded-lg border border-bordure-defaut bg-fond-surface p-6">
            <div class="flex items-baseline justify-between">
              <h2 class="text-base leading-6 font-bold text-texte-titre">Qui le porte</h2>
              <span class="text-xs leading-5 text-texte-mention">{{ a.cosignataires.length + 1 }} signataires</span>
            </div>
            <div class="rounded bg-fond-page px-3 py-2">
              <p class="text-sm leading-6 font-bold" :style="{ color: a.couleur }">{{ a.auteur }}</p>
              <p class="text-xs leading-5 text-texte-mention">{{ a.groupe || 'Groupe inconnu' }} - auteur</p>
            </div>
            <ul class="flex max-h-[480px] flex-col gap-1 overflow-y-auto text-sm leading-6 text-texte-defaut">
              <li v-for="s in a.cosignataires" :key="s">{{ s }}</li>
            </ul>
          </aside>
        </div>
      </template>
    </main>
  </div>
</template>
