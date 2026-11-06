<script setup lang="ts">
import type { Texte } from '~/utils/api'

defineProps<{ texte: Texte }>()
</script>

<template>
  <CarteResultat compacte>
    <div class="flex gap-2">
      <span v-if="texte.procedure" class="badge bg-fond-selection text-texte-titre">{{ texte.procedure }}</span>
      <span v-if="texte.etat" class="badge bg-fond-neutre">{{ texte.etat }}</span>
    </div>
    <a href="#" class="lien-titre text-xl leading-7">{{ texte.titre }}</a>
    <p v-if="texte.depot" class="text-sm leading-6 text-texte-mention">Déposé le {{ texte.depot }}</p>
    <p class="text-sm leading-6">{{ texte.amendements }} amendements correspondant à la recherche</p>
  </CarteResultat>
</template>
