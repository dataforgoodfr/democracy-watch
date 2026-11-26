import { defineConfig } from 'vitest/config'
import { defineVitestProject } from '@nuxt/test-utils/config'
import { fileURLToPath } from 'node:url'

const fromRoot = (path: string) => fileURLToPath(new URL(path, import.meta.url))

const nuxtAliases = {
  '~~': fromRoot('./'),
  '@@': fromRoot('./'),
  '~': fromRoot('./app'),
  '@': fromRoot('./app'),
  '#shared': fromRoot('./shared'),
  '#server': fromRoot('./server')
}

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['tests/unit/**/*.{test,spec}.ts'],
          environment: 'node'
        },
        resolve: { alias: nuxtAliases }
      },
      await defineVitestProject({
        test: {
          name: 'integration',
          include: ['tests/integration/**/*.{test,spec}.ts'],
          environment: 'nuxt'
        }
      }),
      {
        test: {
          name: 'e2e',
          include: ['tests/e2e/**/*.{test,spec}.ts'],
          environment: 'node',
          testTimeout: 60_000,
          hookTimeout: 120_000
        },
        resolve: { alias: nuxtAliases }
      }
    ]
  }
})
