import { createHash, timingSafeEqual } from 'node:crypto'

// Accès protégé par un mot de passe unique partagé (variable d'env SITE_PASSWORD).
// Le cookie contient une empreinte du mot de passe, jamais le mot de passe lui-même :
// changer SITE_PASSWORD déconnecte tout le monde.
export const COOKIE = 'dw_session'

function empreinte(valeur: string): Buffer {
  return createHash('sha256').update(`democracy-watch:${valeur}`).digest()
}

/** Jeton attendu dans le cookie ; vide si SITE_PASSWORD n'est pas définie (tout est refusé). */
export function jetonAttendu(): string {
  const mdp = process.env.SITE_PASSWORD
  return mdp ? empreinte(mdp).toString('hex') : ''
}

function egaux(a: string, b: string): boolean {
  const [x, y] = [Buffer.from(a), Buffer.from(b)]
  return x.length === y.length && timingSafeEqual(x, y)
}

export function motDePasseValide(saisi: string): boolean {
  const attendu = jetonAttendu()
  return Boolean(attendu) && egaux(empreinte(saisi).toString('hex'), attendu)
}

export function sessionValide(jeton: string | undefined): boolean {
  const attendu = jetonAttendu()
  return Boolean(attendu && jeton) && egaux(jeton!, attendu)
}
