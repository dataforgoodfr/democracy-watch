<script setup lang="ts">
import { sigleGroupe, type Amendement } from '~/utils/api'

defineProps<{ amendement: Amendement }>()
</script>

<template>
  <CarteResultat :to="`/amendements/${amendement.uid}`">
    <div class="flex w-full items-center justify-between gap-2">
      <span class="text-base leading-6 font-bold text-texte-titre">{{ amendement.numero }}</span>
      <BadgeSort :sort="amendement.sort" />
    </div>
    <div class="flex items-center gap-2 text-sm leading-6">
      <span class="size-2 rounded-full" :style="{ backgroundColor: amendement.couleur }" />
      <strong :style="{ color: amendement.couleur }">
        {{ amendement.auteur }}<template v-if="amendement.groupe"> ({{ sigleGroupe(amendement.groupe) }})</template>
      </strong>
    </div>
    <p class="text-sm leading-6 text-texte-mention">
      <span class="text-texte-action underline">{{ amendement.cible }}</span> - {{ amendement.texte }}
    </p>
    <div class="w-full rounded bg-fond-page px-3 py-2">
      <TexteLoi :segments="amendement.modification" class="line-clamp-3" />
    </div>
  </CarteResultat>
</template>
