import { test, expect } from '@playwright/test';

test('Generate → History → Open', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/.+/);

  // 1) Промпт (textarea#prompt)
  await page.locator('#prompt').fill('a cat');

  // 2) Кнопка «Сгенерировать»
  const generateBtn = page.getByRole('button', { name: 'Сгенерировать' });
  await Promise.all([
    page.waitForResponse(r => r.url().includes('/generate') && [200, 201, 202].includes(r.status())),
    generateBtn.click(),
  ]);

  // 3) Вкладка «История»
  await page.getByRole('tab', { name: 'История' }).click();

  // 4) Первая ссылка на файл в истории: <a href="/file?path=...">
  const firstLink = page.locator('a[href^="/file"]').first();
  await firstLink.waitFor({ state: 'visible', timeout: 30000 });

  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    firstLink.click(),
  ]);
  await popup.waitForLoadState('domcontentloaded');
  await expect(popup).toHaveURL(/\/file\?path=/);
  await expect(popup.locator('img')).toBeVisible();
});
