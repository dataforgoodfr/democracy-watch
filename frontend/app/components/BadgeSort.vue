<script setup lang="ts">
import { SORTS } from '~/utils/api'

// Sort de l'amendement (Adopté, Rejeté…) : badge coloré avec icône, neutre pour les sorts non prévus.
const props = defineProps<{ sort: string }>()
const style = computed(() => SORTS[props.sort])
</script>

<template>
  <span v-if="style" class="badge rounded px-2 py-0.5" :class="style.classes">
    <img :src="`/icons/${style.icone}.svg`" alt="" width="12" height="12" />
    {{ style.libelle }}
  </span>
  <span v-else-if="sort" class="badge rounded bg-fond-neutre px-2 py-0.5">{{ sort }}</span>
</template>
