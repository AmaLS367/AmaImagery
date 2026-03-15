import { expect, test } from '@playwright/test'

test('generate flow completes with mocked lifecycle', async ({ page }) => {
  let statusCalls = 0

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
  })
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'unauthorized' }) })
  })
  await page.route('**/api/v1/images/generate', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ task_id: 'task-1', status: 'queued' }),
    })
  })
  await page.route('**/api/v1/images/status/task-1', async (route) => {
    statusCalls += 1
    const payload =
      statusCalls < 2
        ? { task_id: 'task-1', status: 'running', image_filename: null }
        : { task_id: 'task-1', status: 'completed', image_filename: 'result.png', exp: 1, sig: 'sig' }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    })
  })
  await page.route('**/api/v1/file**', async (route) => {
    await route.fulfill({ status: 200, body: 'image' })
  })

  await page.goto('/generate')
  await page.getByPlaceholder('Fashion portrait in editorial midnight studio, precise eyes, quiet confidence, polished chrome accents.').fill('E2E runtime portrait')
  await page.getByRole('button', { name: 'Generate' }).click()

  await expect(page.getByText('Generation completed')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Download image' })).toBeVisible()
})
