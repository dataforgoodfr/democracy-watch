// Vérifie le mot de passe partagé et pose le cookie de session (30 jours).
export default defineEventHandler(async (event) => {
  const { motDePasse } = await readBody<{ motDePasse?: string }>(event)
  if (!motDePasseValide(motDePasse ?? '')) {
    throw createError({ statusCode: 401, statusMessage: 'Mot de passe incorrect' })
  }
  setCookie(event, COOKIE, jetonAttendu(), {
    httpOnly: true,
    sameSite: 'lax',
    secure: !import.meta.dev,
    maxAge: 60 * 60 * 24 * 30,
    path: '/',
  })
  return { ok: true }
})
