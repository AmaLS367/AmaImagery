import { defineConfig } from '@playwright/test'

const port = process.env.PLAYWRIGHT_PORT || '4173'

export default defineConfig({
  testDir: './playwright',
  use: {
    baseURL: process.env.BASE_URL || `http://127.0.0.1:${port}`,
  },
  webServer: {
    command: `npm --prefix ../../../frontend run dev -- --host 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
