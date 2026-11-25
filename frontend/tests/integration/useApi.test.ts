import { afterEach, expect, it, vi } from 'vitest'
import { useApi } from '~/composables/useApi'

afterEach(() => {
  vi.restoreAllMocks()
})

it("crée un client ciblant l'URL publique de l'API côté navigateur", () => {
  const create = vi.spyOn($fetch, 'create')

  useApi()

  expect(create).toHaveBeenCalledWith({ baseURL: 'http://localhost:8000' })
})
