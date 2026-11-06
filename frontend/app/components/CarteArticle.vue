<script setup lang="ts">
import type { Article } from '~/utils/api'

defineProps<{ article: Article }>()
</script>

<template>
  <CarteResultat>
    <span class="text-base leading-6 font-bold text-texte-accent">{{ article.libelle }}</span>
    <p class="text-sm leading-6 text-texte-mention">{{ article.dossier }}</p>
    <blockquote v-if="article.extrait.length" class="w-full border-l-2 border-bordure-defaut pl-3">
      <TexteLoi :segments="article.extrait" class="line-clamp-3" />
    </blockquote>
    <p class="pt-1 text-sm leading-6 font-bold text-statut-avertissement">
      {{ article.amendements }} amendements correspondant à la recherche
    </p>
  </CarteResultat>
</template>
