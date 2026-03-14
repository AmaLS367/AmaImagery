import { test, expect } from '@playwright/test';

test('Generate -> History route flow', async ({ page }) => {
  await page.goto('/generate');
  await expect(page).toHaveTitle(/.+/);
  await expect(
    page.getByRole('heading', { name: /Main product shell with preserved IA and internal state variants\./i }),
  ).toBeVisible();

  await page.locator('#prompt').fill('a cat');

  const generateBtn = page.getByRole('button', { name: /^Generate$/ });
  await Promise.all([
    page.waitForResponse((response) => response.url().includes('/api/v1/images/generate') && [200, 201, 202].includes(response.status())),
    generateBtn.click(),
  ]);

  await page.goto('/history');
  await expect(page).toHaveURL(/\/history$/);
  await expect(
    page.getByRole('heading', { name: /Searchable history with filters, metadata, and explicit state handling\./i }),
  ).toBeVisible();

  await page.getByRole('button', { name: /^Refresh$/ }).click();
  await expect(page.getByText('a cat').first()).toBeVisible({ timeout: 30000 });

  const firstImage = page.locator('article img').first();
  await expect(firstImage).toBeVisible({ timeout: 30000 });
});
