<script setup lang="ts">
  const routeQuery = useSearchQuery()
  const query = ref(routeQuery.value)
  watch(routeQuery, value => (query.value = value))

  async function submit() {
    const q = query.value.trim()
    if (!q) return
    await navigateTo({ path: '/recherche', query: { q } })
  }
</script>

<template>
  <form
    role="search"
    class="flex w-full min-w-0 items-center gap-3"
    @submit.prevent="submit"
  >
    <UInput
      v-model="query"
      icon="i-lucide-search"
      placeholder="Rechercher un texte de loi, un amendement, un article"
      aria-label="Rechercher"
      class="min-w-0 flex-1"
      :ui="{
        base: 'h-12 rounded-dw-sm bg-(--dw-fond-surface) text-base ring-0 border border-(--dw-bordure-forte) placeholder:text-(--dw-texte-mention)'
      }"
      data-testid="search-input"
    >
      <template v-if="query" #trailing>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="link"
          size="sm"
          aria-label="Effacer la recherche"
          class="text-(--dw-texte-mention) hover:text-(--dw-texte-defaut)"
          data-testid="search-clear"
          @click="query = ''"
        />
      </template>
    </UInput>
    <button type="submit" class="dw-btn h-12 shrink-0 font-bold">
      Rechercher
    </button>
  </form>
</template>
