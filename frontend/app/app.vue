<script setup lang="ts">
  const siteName = 'Democracy Watch'
  useHead({
    titleTemplate: title => (title ? `${title} · ${siteName}` : siteName)
  })
</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
