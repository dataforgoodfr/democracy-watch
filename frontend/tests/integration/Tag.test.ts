import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import Tag from '@/components/tag/Tag.vue'

describe('Tag', () => {
  describe('non cliquable', () => {
    it('affiche le libellé dans un paragraphe par défaut', async () => {
      const wrapper = await mountSuspended(Tag, { props: { label: 'Santé' } })
      const tag = wrapper.get('p.dw-tag')
      expect(tag.text()).toBe('Santé')
    })

    it("n'affiche pas d'icône par défaut", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Santé', type: 'default' }
      })
      expect(wrapper.find('[data-testid=tag-icon]').exists()).toBe(false)
    })

    it("affiche l'icône à gauche quand hasIcon est vrai", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Santé',
          type: 'default',
          hasIcon: true,
          icon: 'i-lucide-info'
        }
      })
      expect(wrapper.find('[data-testid=tag-icon]').exists()).toBe(true)
    })
  })

  describe('cliquable', () => {
    it('affiche un lien vers href', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Retraites', type: 'clickable', href: '/recherche' }
      })
      const link = wrapper.get('a.dw-tag')
      expect(link.attributes('href')).toBe('/recherche')
      expect(link.text()).toBe('Retraites')
      expect(link.attributes('target')).toBeUndefined()
    })

    it('ouvre un nouvel onglet avec un titre quand blank est vrai', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Retraites',
          type: 'clickable',
          href: 'https://www.assemblee-nationale.fr',
          blank: true,
          attributes: { title: 'Retraites - nouvelle fenêtre' }
        }
      })
      const link = wrapper.get('a')
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toContain('noopener')
      expect(link.attributes('title')).toBe('Retraites - nouvelle fenêtre')
    })

    it('applique le titre fourni sans nouvel onglet', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Retraites',
          type: 'clickable',
          href: '/recherche',
          attributes: { title: 'Voir les textes sur les retraites' }
        }
      })
      const link = wrapper.get('a')
      expect(link.attributes('title')).toBe('Voir les textes sur les retraites')
      expect(link.attributes('target')).toBeUndefined()
    })

    it("applique la couleur d'accentuation", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Retraites',
          type: 'clickable',
          href: '/recherche',
          accent: 'jaune'
        }
      })
      expect(wrapper.get('a').classes()).toContain('dw-tag--jaune')
    })

    it("retire le href et signale l'état quand il est désactivé", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Retraites',
          type: 'clickable',
          href: '/recherche',
          disabled: true
        }
      })
      const link = wrapper.get('a.dw-tag')
      expect(link.attributes('href')).toBeUndefined()
      expect(link.attributes('role')).toBe('link')
      expect(link.attributes('aria-disabled')).toBe('true')
    })

    it("affiche l'icône à gauche quand hasIcon est vrai", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Retraites',
          type: 'clickable',
          href: '/recherche',
          hasIcon: true,
          icon: 'i-lucide-arrow-left'
        }
      })
      expect(wrapper.find('a [data-testid=tag-icon]').exists()).toBe(true)
    })
  })

  describe('sélectionnable', () => {
    it('est un bouton non pressé quand pressed est faux', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Adopté', type: 'selectable', pressed: false }
      })
      const button = wrapper.get('button.dw-tag')
      expect(button.attributes('type')).toBe('button')
      expect(button.attributes('aria-pressed')).toBe('false')
      expect(wrapper.find('[data-testid=tag-check]').exists()).toBe(false)
    })

    it('est pressé avec une coche quand pressed est vrai', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Adopté', type: 'selectable', pressed: true }
      })
      expect(wrapper.get('button').attributes('aria-pressed')).toBe('true')
      expect(wrapper.find('[data-testid=tag-check]').exists()).toBe(true)
    })

    it('émet la nouvelle valeur de pressed au clic', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Adopté', type: 'selectable', pressed: false }
      })
      await wrapper.get('button').trigger('click')
      expect(wrapper.emitted('update:pressed')).toEqual([[true]])
    })

    it("bascule l'état avec v-model:pressed", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Adopté',
          type: 'selectable',
          pressed: false,
          'onUpdate:pressed': (pressed: boolean) =>
            wrapper.setProps({ pressed })
        }
      })
      const button = wrapper.get('button')
      await button.trigger('click')
      expect(button.attributes('aria-pressed')).toBe('true')
      await button.trigger('click')
      expect(button.attributes('aria-pressed')).toBe('false')
    })

    it("n'émet rien quand il est désactivé", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Adopté',
          type: 'selectable',
          pressed: false,
          disabled: true
        }
      })
      const button = wrapper.get('button')
      expect(button.attributes('disabled')).toBeDefined()
      await button.trigger('click')
      expect(wrapper.emitted('update:pressed')).toBeUndefined()
    })

    it("affiche l'icône à gauche quand hasIcon est vrai", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: {
          label: 'Adopté',
          type: 'selectable',
          pressed: false,
          hasIcon: true,
          icon: 'i-lucide-info'
        }
      })
      expect(wrapper.find('button [data-testid=tag-icon]').exists()).toBe(true)
    })
  })

  describe('supprimable', () => {
    it('est un bouton avec un libellé explicite et une croix', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Écologie', type: 'deletable' }
      })
      const button = wrapper.get('button.dw-tag')
      expect(button.attributes('type')).toBe('button')
      expect(button.attributes('aria-label')).toBe('Retirer le filtre Écologie')
      expect(button.attributes('aria-pressed')).toBeUndefined()
      expect(wrapper.find('[data-testid=tag-delete]').exists()).toBe(true)
      expect(wrapper.find('[data-testid=tag-icon]').exists()).toBe(false)
    })

    it("émet l'événement delete au clic", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Écologie', type: 'deletable' }
      })
      await wrapper.get('button').trigger('click')
      expect(wrapper.emitted('delete')).toHaveLength(1)
    })

    it("n'émet rien quand il est désactivé", async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Écologie', type: 'deletable', disabled: true }
      })
      const button = wrapper.get('button')
      expect(button.attributes('disabled')).toBeDefined()
      await button.trigger('click')
      expect(wrapper.emitted('delete')).toBeUndefined()
    })
  })

  describe('taille', () => {
    it('est en taille MD par défaut', async () => {
      const wrapper = await mountSuspended(Tag, { props: { label: 'Santé' } })
      expect(wrapper.get('.dw-tag').classes()).not.toContain('dw-tag--sm')
    })

    it('applique la taille SM', async () => {
      const wrapper = await mountSuspended(Tag, {
        props: { label: 'Santé', size: 'sm' }
      })
      expect(wrapper.get('.dw-tag').classes()).toContain('dw-tag--sm')
    })
  })
})
