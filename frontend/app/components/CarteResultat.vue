<script setup lang="ts">
// Carte blanche commune aux résultats (texte, article, amendement), flèche à droite.
// Avec `to`, toute la carte est un lien vers cette page.
withDefaults(defineProps<{ compacte?: boolean; to?: string }>(), { compacte: false, to: undefined })
const NuxtLink = resolveComponent('NuxtLink')
</script>

<template>
  <component
    :is="to ? NuxtLink : 'article'"
    :to="to"
    class="flex w-full cursor-pointer items-center gap-6 rounded-lg border border-bordure-defaut bg-fond-surface px-6 hover:border-bordure-forte"
    :class="compacte ? 'py-6' : 'py-4'"
  >
    <div class="flex min-w-0 flex-1 flex-col items-start gap-2">
      <slot />
    </div>
    <img src="/icons/fleche.svg" alt="" width="24" height="24" class="shrink-0" />
  </component>
</template>
