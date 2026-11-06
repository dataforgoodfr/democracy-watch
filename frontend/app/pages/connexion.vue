<script setup lang="ts">
// Page de connexion (maquette « Connexion/inscription », allégée) : un seul mot de passe partagé.
const route = useRoute()
// Seulement un chemin local (« /… »), pour ne pas rediriger vers un autre site
const retour = computed(() => {
  const r = String(route.query.retour ?? '/')
  return r.startsWith('/') && !r.startsWith('//') ? r : '/'
})
const motDePasse = ref('')
const visible = ref(false)
const erreur = ref('')
const envoi = ref(false)

async function connecter() {
  erreur.value = ''
  envoi.value = true
  try {
    await $fetch('/api/connexion', { method: 'POST', body: { motDePasse: motDePasse.value } })
    await navigateTo(retour.value)
  } catch {
    erreur.value = 'Mot de passe incorrect.'
  } finally {
    envoi.value = false
  }
}

useHead({ title: 'Connexion - Democracy Watch' })
</script>

<template>
  <div class="grid min-h-screen grid-cols-2">
    <div class="flex flex-col bg-fond-marque px-16 py-14">
      <div class="flex items-center gap-1">
        <img src="/icons/logo.svg" alt="" width="56" height="56" />
        <span class="font-marque text-[22px] leading-7 font-extrabold tracking-[-0.44px] text-texte-action italic">
          Democracy Watch
        </span>
      </div>
      <div class="my-auto flex flex-col gap-8">
        <p class="font-marque text-[44px] leading-[52px] font-extrabold text-texte-defaut italic">
          Gardez un oeil sur vos amendements
        </p>
        <ul class="flex max-w-[480px] list-disc flex-col gap-4 pl-5 text-base leading-6 text-texte-defaut">
          <li>Suivez tous les amendements d'un texte, regroupés par article visé</li>
          <li>Triez et filtrez les amendements qui correspondent à votre sujet</li>
          <li>Repérez plus facilement les intérêts qui pourraient se cacher derrière certains amendements</li>
        </ul>
      </div>
    </div>

    <div class="flex items-center justify-center bg-fond-marque/50 px-16">
      <form class="flex w-full max-w-[440px] flex-col gap-6" @submit.prevent="connecter">
        <div class="flex flex-col gap-2">
          <h1 class="text-[40px] leading-[48px] font-bold text-texte-titre">Connexion</h1>
          <p class="text-sm leading-6 text-texte-mention">Accédez à l'espace Democracy Watch.</p>
        </div>
        <label class="flex flex-col gap-2">
          <span class="text-sm leading-6 font-bold text-texte-titre">Mot de passe</span>
          <span
            class="flex h-12 items-center gap-2 rounded-lg border border-bordure-forte bg-fond-surface px-4 focus-within:outline-2 focus-within:outline-statut-info"
          >
            <input
              v-model="motDePasse"
              :type="visible ? 'text' : 'password'"
              autocomplete="current-password"
              required
              autofocus
              class="flex-1 text-base leading-6 text-texte-titre outline-none"
            />
            <button
              type="button"
              class="text-sm leading-6 text-texte-action underline"
              :aria-pressed="visible"
              @click="visible = !visible"
            >
              {{ visible ? 'Masquer' : 'Afficher' }}
            </button>
          </span>
        </label>
        <p v-if="erreur" role="alert" class="text-sm leading-6 font-bold text-statut-erreur">{{ erreur }}</p>
        <button
          type="submit"
          :disabled="envoi"
          class="h-12 rounded bg-fond-action px-4 text-base leading-6 font-bold text-texte-inverse disabled:opacity-60"
        >
          Se connecter
        </button>
      </form>
    </div>
  </div>
</template>
