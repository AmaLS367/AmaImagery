import { expect, test } from '@playwright/test'

test('settings persist locally across reloads', async ({ page }) => {
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
  })
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
  })

  await page.goto('/settings')
  await page.getByText('Cinematic').click()
  const accentInput = page.locator('input[value^="#"]').first()
  await accentInput.fill('#EF4444')
  await page.reload()

  await expect(accentInput).toHaveValue('#EF4444')
  await expect.poll(async () => page.evaluate(() => document.documentElement.dataset.visualMode)).toBe('cinematic')
})
