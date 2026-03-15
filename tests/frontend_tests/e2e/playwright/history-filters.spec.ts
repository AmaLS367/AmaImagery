import { expect, test } from '@playwright/test'

test('history filters work against mocked backend data', async ({ page }) => {
  await page.route('**/api/v1/auth/me', async (route) => {
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

  await page.route('**/api/v1/users/me/generations**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          {
            id: 'one',
            image_path: 'one.png',
            image_filename: 'one.png',
            prompt: { prompt: 'Portrait alpha' },
            params: { width: 1024, height: 1024, guidance_scale: 7, steps: 28 },
            created_at: '2026-03-01T12:00:00.000Z',
            provider_name: 'AmaFusion',
          },
          {
            id: 'two',
            image_path: 'two.png',
            image_filename: 'two.png',
            prompt: { prompt: 'Landscape beta' },
            params: { width: 1024, height: 576, guidance_scale: 9, steps: 30 },
            created_at: '2026-03-02T12:00:00.000Z',
            provider_name: 'AmaFusion',
          },
        ],
      }),
    })
  })

  await page.goto('/history')
  await expect(page.getByText('Portrait alpha').first()).toBeVisible()

  await page.getByPlaceholder('Search generations...').fill('landscape')
  await expect(page.getByText('Landscape beta').first()).toBeVisible()
  await expect(page.getByText('Portrait alpha').first()).toHaveCount(0)
})
