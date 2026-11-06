<script setup lang="ts">
import type { Segment } from '~/utils/api'

// Extrait de loi en Spectral : termes recherchés surlignés, suppressions / ajouts colorés.
defineProps<{ segments: Segment[] }>()
</script>

<template>
  <p class="font-loi text-base leading-7 text-texte-defaut">
    <template v-for="(s, i) in segments" :key="i">
      <mark v-if="s.k === 'mark'" class="bg-transparent font-semibold text-texte-accent">{{ s.t }}</mark>
      <del v-else-if="s.k === 'del'" class="font-semibold text-statut-erreur">{{ s.t }}</del>
      <ins v-else-if="s.k === 'ins'" class="font-semibold text-statut-succes no-underline">{{ s.t }}</ins>
      <span v-else>{{ s.t }}</span>
    </template>
  </p>
</template>
