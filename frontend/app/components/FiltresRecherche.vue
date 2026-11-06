<script setup lang="ts">
import { GROUPES } from '~/utils/api'

// Pas de filtre par commission : l'API ne fournit pas la commission des amendements.

const groupes = defineModel<string[]>('groupes', { required: true })

const ouvert = ref(true)

function reinitialiser() {
  groupes.value = []
}
</script>

<template>
  <aside class="flex w-[338px] shrink-0 flex-col gap-4 rounded-lg border border-bordure-defaut bg-fond-surface p-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl leading-8 font-bold text-texte-titre">Filtres</h2>
      <button type="button" class="h-8 px-3 text-sm leading-6 font-bold text-texte-action underline" @click="reinitialiser">
        Réinitialiser
      </button>
    </div>
    <div class="flex flex-col gap-8 py-2">
      <fieldset class="flex flex-col gap-4 px-1">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-2 rounded bg-fond-marque px-4 py-3 text-left text-base leading-6 font-bold text-texte-action"
          :aria-expanded="ouvert"
          @click="ouvert = !ouvert"
        >
          Filtrer par groupe parlementaire (auteur.ice)
          <img src="/icons/chevron.svg" alt="" width="20" height="20" :class="{ 'rotate-180': !ouvert }" />
        </button>
        <div v-show="ouvert" class="flex flex-col gap-1 px-2">
          <label v-for="(groupe, g) in GROUPES" :key="g" class="case font-bold" :style="{ color: groupe.couleur }">
            <input v-model="groupes" type="checkbox" :value="groupe.libelle" />
            ● {{ g }}
          </label>
        </div>
      </fieldset>
    </div>
  </aside>
</template>

<style scoped>
@reference '~/assets/css/main.css';

.case {
  @apply flex cursor-pointer items-start gap-2.5 rounded px-1 py-0.5 text-base leading-6;
}
.case:not(.font-bold) {
  @apply text-texte-titre;
}
.case input {
  @apply size-6 shrink-0 cursor-pointer appearance-none rounded border border-bordure-forte bg-fond-surface bg-center bg-no-repeat;
}
.case input:checked {
  @apply border-fond-action bg-fond-action;
  background-image: url('/icons/check.svg');
}
</style>
