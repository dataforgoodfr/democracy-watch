import { expect, it } from 'vitest'
import { useApi } from '@/composables/useApi'
import { useApi as useApiFromTilde } from '~/composables/useApi'
import pkg from '~~/package.json'

it("résout les alias Nuxt hors de l'environnement Nuxt", () => {
  expect(useApi).toBeTypeOf('function')
  expect(useApiFromTilde).toBe(useApi)
  expect(pkg.name).toBe('democracy-watch-frontend')
})
