import { expect, test } from '@playwright/test'

test('login flow redirects to generate with mocked auth', async ({ page }) => {
  let meCalls = 0

  await page.route('**/api/v1/auth/me', async (route) => {
    meCalls += 1
    if (meCalls === 1) {
      await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-1',
        email: 'tester@example.com',
        username: 'tester',
        settings: {},
      }),
    })
  })

  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
  })

  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-1',
        email: 'tester@example.com',
        username: 'tester',
        access_token: 'cookie-backed',
        token_type: 'bearer',
        expires_in: 900,
      }),
    })
  })

  await page.goto('/login')
  await page.locator('#identifier').fill('tester@example.com')
  await page.locator('#password').fill('password123')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL(/\/generate$/)
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible()
})
