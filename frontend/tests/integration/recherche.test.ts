import { mountSuspended } from '@nuxt/test-utils/runtime'
import { expect, it } from 'vitest'
import RecherchePage from '@/pages/recherche.vue'

it("affiche la requête présente dans l'URL", async () => {
  const wrapper = await mountSuspended(RecherchePage, {
    route: '/recherche?q=retraites'
  })
  expect(wrapper.get('[data-testid=search-query]').text()).toBe('retraites')
})

it('affiche une requête vide sans paramètre q', async () => {
  const wrapper = await mountSuspended(RecherchePage, { route: '/recherche' })
  expect(wrapper.get('[data-testid=search-query]').text()).toBe('')
})
