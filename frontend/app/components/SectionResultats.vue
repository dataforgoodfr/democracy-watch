<script setup lang="ts">
defineProps<{ titre: string; total: number; lienVoirTout: string }>()
</script>

<template>
  <section class="flex w-full flex-col gap-6 py-2">
    <header class="flex items-start gap-2">
      <div class="flex flex-1 items-center gap-2">
        <h2 class="text-2xl leading-8 font-bold text-texte-titre">{{ titre }}</h2>
        <span class="rounded bg-fond-neutre px-2 py-0.5 text-xs leading-5 font-bold tracking-[0.3px] text-texte-defaut">
          {{ total }}
        </span>
      </div>
      <a href="#" class="flex h-8 items-center rounded px-3 py-1 text-sm leading-6 font-bold text-texte-action">
        {{ lienVoirTout }}
      </a>
    </header>
    <div class="flex flex-col gap-4">
      <slot />
    </div>
  </section>
</template>
