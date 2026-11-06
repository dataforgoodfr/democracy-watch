// Relais /api/v0/* vers l'API : la clé (variable d'env API_KEY) est ajoutée côté serveur
// Nuxt et n'arrive jamais dans le navigateur.
export default defineEventHandler((event) => {
  const { apiBase } = useRuntimeConfig(event)
  return proxyRequest(event, apiBase + event.path, { headers: { 'X-API-Key': process.env.API_KEY ?? '' } })
})
