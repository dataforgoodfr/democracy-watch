import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  devtools: { enabled: false },
  // Surchargée par NUXT_API_BASE ; la clé est lue dans API_KEY par server/api/v0/[...path].ts
  runtimeConfig: { apiBase: 'https://dw-api.services.d4g.fr' },
  css: ['~/assets/css/main.css'],
  vite: { plugins: [tailwindcss()] },
  app: {
    head: {
      htmlAttrs: { lang: 'fr' },
      title: 'Democracy Watch',
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,700;1,800&family=DM+Sans:opsz,wght@9..40,400;9..40,700&family=Spectral:wght@400;600&display=swap',
        },
      ],
    },
  },
})
