import { defineConfig } from "@playwright/test";
import { E2E_PORTS } from "./e2e/ports.ts";

// Les sites doivent être construits avant : `pnpm build`.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  fullyParallel: true,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    headless: true,
    viewport: { width: 1440, height: 900 },
    locale: "fr-FR",
  },
  webServer: [
    {
      command: `pnpm --filter @democracy-watch/web exec next start --port ${E2E_PORTS.web}`,
      port: E2E_PORTS.web,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `pnpm --filter @democracy-watch/docs exec zudoku preview --port ${E2E_PORTS.docs}`,
      port: E2E_PORTS.docs,
      reuseExistingServer: !process.env.CI,
    },
  ],
  projects: [
    {
      name: "web",
      testMatch: /web\..*\.spec\.ts/,
      use: { browserName: "chromium", baseURL: `http://localhost:${E2E_PORTS.web}` },
    },
    {
      name: "docs",
      testMatch: /docs\..*\.spec\.ts/,
      use: { browserName: "chromium", baseURL: `http://localhost:${E2E_PORTS.docs}` },
    },
  ],
});
