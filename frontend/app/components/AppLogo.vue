<script setup lang="ts">
  import symbole from '~/assets/img/logo-symbole.svg'
</script>

<template>
  <NuxtLink
    to="/"
    class="flex shrink-0 items-center gap-1"
    aria-label="Democracy Watch, accueil"
  >
    <img :src="symbole" alt="" width="56" height="56" />
    <span
      class="text-[22px] leading-7 font-extrabold tracking-[-0.02em] text-(--dw-texte-action) italic"
    >
      Democracy Watch
    </span>
  </NuxtLink>
</template>
