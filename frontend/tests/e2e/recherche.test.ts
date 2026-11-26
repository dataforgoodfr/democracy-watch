import { createPage, setup, url } from '@nuxt/test-utils/e2e'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

describe('recherche', async () => {
  await setup({
    rootDir: fileURLToPath(new URL('../..', import.meta.url)),
    browser: true
  })

  it("mène de l'accueil à la page de résultats", async () => {
    const page = await createPage('/')
    await page.getByTestId('search-input').fill('retraites')
    await page.getByRole('button', { name: 'Rechercher' }).click()
    await page.waitForURL(url('/recherche?q=retraites'))
    expect(await page.getByTestId('search-query').textContent()).toBe(
      'retraites'
    )
    expect(await page.title()).toBe('Recherche : retraites · Democracy Watch')
  })
})
