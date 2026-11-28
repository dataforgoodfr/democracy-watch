import { mountSuspended } from '@nuxt/test-utils/runtime'
import { expect, it, describe } from 'vitest'
import AppLogo from '@/components/AppLogo.vue'

describe('AppLogo', () => {
  it('should have a link to home page', async () => {
    const wrapper = await mountSuspended(AppLogo)
    const link = wrapper.get('a')
    expect(link.attributes('href')).toBe('/')
    expect(link.attributes('aria-label')).toMatch(/democracy watch/i)
  })
})
