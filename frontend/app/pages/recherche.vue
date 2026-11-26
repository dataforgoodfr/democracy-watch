<script setup lang="ts">
  const q = useSearchQuery()
  useHead({
    title: computed(() => (q.value ? `Recherche : ${q.value}` : 'Recherche'))
  })
</script>

<template>
  <section>
    <h1 class="text-2xl font-bold text-highlighted">Recherche</h1>
    <p class="mt-2 text-muted" data-testid="search-query">{{ q }}</p>
  </section>
</template>
