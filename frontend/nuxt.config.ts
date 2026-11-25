export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@nuxt/icon', '@nuxt/fonts', '@pinia/nuxt'],
  css: ['~/assets/css/main.css'],
  fonts: {
    defaults: {
      weights: [400, 500, 700, 800],
      styles: ['normal', 'italic']
    }
  },
  app: {
    head: {
      htmlAttrs: { lang: 'fr' },
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        {
          rel: 'icon',
          type: 'image/png',
          sizes: '96x96',
          href: '/favicon-96x96.png'
        },
        { rel: 'icon', href: '/favicon.ico', sizes: '48x48' },
        {
          rel: 'apple-touch-icon',
          sizes: '180x180',
          href: '/apple-touch-icon.png'
        },
        { rel: 'manifest', href: '/site.webmanifest' }
      ],
      meta: [{ name: 'theme-color', content: '#f7fbdd' }]
    }
  },
  runtimeConfig: {
    api: { url: '' },
    public: {
      api: { url: 'http://localhost:8000' }
    }
  }
})
