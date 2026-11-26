import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { beforeEach, expect, it, vi } from 'vitest'
import AppHeader from '@/components/AppHeader.vue'

const { navigateToMock } = vi.hoisted(() => ({
  navigateToMock: vi.fn<(to: unknown) => void>()
}))
mockNuxtImport('navigateTo', () => navigateToMock)

beforeEach(() => {
  navigateToMock.mockClear()
})

it('affiche le logo et la barre de recherche', async () => {
  const wrapper = await mountSuspended(AppHeader)
  expect(
    wrapper.get('a[aria-label^="Democracy Watch"]').attributes('href')
  ).toBe('/')
  wrapper.get('form[role=search]')
})

it('redirige vers /recherche avec la requête saisie', async () => {
  const wrapper = await mountSuspended(AppHeader)
  await wrapper.get('[data-testid=search-input]').setValue('  retraites ')
  await wrapper.get('form').trigger('submit')
  expect(navigateToMock).toHaveBeenCalledWith({
    path: '/recherche',
    query: { q: 'retraites' }
  })
})

it('ignore une recherche vide', async () => {
  const wrapper = await mountSuspended(AppHeader)
  await wrapper.get('form').trigger('submit')
  expect(navigateToMock).not.toHaveBeenCalled()
})

it("ignore une recherche composée uniquement d'espaces", async () => {
  const wrapper = await mountSuspended(AppHeader)
  await wrapper.get('[data-testid=search-input]').setValue('   ')
  await wrapper.get('form').trigger('submit')
  expect(navigateToMock).not.toHaveBeenCalled()
})

it('affiche le symbole du logo et le bouton Rechercher', async () => {
  const wrapper = await mountSuspended(AppHeader)
  wrapper.get('a[aria-label^="Democracy Watch"] img')
  expect(wrapper.get('button[type=submit]').text()).toBe('Rechercher')
})

it('efface la recherche avec le bouton croix', async () => {
  const wrapper = await mountSuspended(AppHeader)
  expect(wrapper.find('[data-testid=search-clear]').exists()).toBe(false)
  const input = wrapper.get<HTMLInputElement>('[data-testid=search-input]')
  await input.setValue('retraites')
  await wrapper.get('[data-testid=search-clear]').trigger('click')
  expect(input.element.value).toBe('')
  expect(wrapper.find('[data-testid=search-clear]').exists()).toBe(false)
})

it("reprend la requête de l'URL quand la route change", async () => {
  const wrapper = await mountSuspended(AppHeader, { route: '/recherche?q=a' })
  const input = wrapper.get<HTMLInputElement>('[data-testid=search-input]')
  expect(input.element.value).toBe('a')
  await useRouter().push('/recherche?q=retraites')
  await nextTick()
  expect(input.element.value).toBe('retraites')
})
