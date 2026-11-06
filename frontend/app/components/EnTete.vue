<script setup lang="ts">
const recherche = defineModel<string>({ required: true })
const emit = defineEmits<{ rechercher: [] }>()
defineProps<{ avertissement?: string }>()
</script>

<template>
  <header class="border-b border-bordure-defaut bg-fond-marque">
    <!-- items-start + -my-1 : le logo (56px) reste centré sur la barre (48px) quand l'avertissement s'affiche -->
    <div class="flex items-start gap-8 px-10 py-4">
      <NuxtLink to="/" class="-my-1 flex shrink-0 items-center gap-1">
        <img src="/icons/logo.svg" alt="" width="56" height="56" />
        <span class="font-marque text-[22px] leading-7 font-extrabold tracking-[-0.44px] text-texte-action italic">
          Democracy Watch
        </span>
      </NuxtLink>
      <div class="flex flex-1 flex-col gap-2">
        <form class="flex items-center gap-3" role="search" @submit.prevent="emit('rechercher')">
          <label
            class="flex h-12 flex-1 items-center gap-3 rounded border border-bordure-forte bg-fond-surface px-4 focus-within:outline-2 focus-within:outline-statut-info"
          >
            <img src="/icons/recherche.svg" alt="" width="16" height="16" />
            <input
              v-model="recherche"
              type="search"
              aria-label="Rechercher"
              class="flex-1 font-marque text-base leading-6 text-texte-titre outline-none"
            />
          </label>
          <button
            type="submit"
            class="h-12 rounded bg-fond-action px-4 py-2 font-marque text-base leading-6 font-bold text-texte-inverse"
          >
            Rechercher
          </button>
        </form>
        <p
          v-if="avertissement"
          role="status"
          class="self-start rounded bg-statut-avertissement-fond px-3 py-1 text-sm leading-6 font-bold text-statut-avertissement"
        >
          ⚠ {{ avertissement }}
        </p>
      </div>
    </div>
  </header>
</template>
