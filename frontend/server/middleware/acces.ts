// Bloque tout le site (pages et /api/v0) tant que le cookie de session n'est pas valide.
// Restent ouverts : la page de connexion, sa route et les fichiers statiques.
const OUVERTS = ['/connexion', '/api/connexion', '/_nuxt/', '/icons/', '/favicon.ico']

export default defineEventHandler((event) => {
  const chemin = event.path.split('?')[0]!
  if (OUVERTS.some((p) => chemin === p || (p.endsWith('/') && chemin.startsWith(p)))) return
  if (sessionValide(getCookie(event, COOKIE))) return
  if (chemin.startsWith('/api/')) {
    throw createError({ statusCode: 401, statusMessage: 'Connexion requise' })
  }
  // Après connexion, on revient à la page demandée
  return sendRedirect(event, `/connexion?retour=${encodeURIComponent(event.path)}`)
})
