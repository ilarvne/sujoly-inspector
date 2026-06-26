import { test, expect } from './auth-fixture';

test('RU locale renders Russian text', async ({ page }) => {
  await page.goto('/ru');
  await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 });
  await expect(page.locator('h1')).toContainText(/Каталог/i);
});

test('KK locale renders Kazakh text', async ({ page }) => {
  await page.goto('/kk');
  await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 });
  await expect(page.locator('h1')).toContainText(/каталогы/i);
});

test('EN locale renders English text', async ({ page }) => {
  await page.goto('/en');
  await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 });
  await expect(page.locator('h1')).toContainText(/Catalog/i);
});

test('language switcher navigates from RU to KK', async ({ page }) => {
  await page.goto('/ru');
  await page.locator('[data-testid="language-switcher"]').selectOption('kk');
  await expect(page).toHaveURL(/\/kk/);
  await expect(page.locator('h1')).toContainText(/каталогы/i);
});

test('language switcher navigates from KK to EN', async ({ page }) => {
  await page.goto('/kk');
  await page.locator('[data-testid="language-switcher"]').selectOption('en');
  await expect(page).toHaveURL(/\/en/);
  await expect(page.locator('h1')).toContainText(/Catalog/i);
});

test('invalid locale returns 404', async ({ page }) => {
  const response = await page.goto('/fr');
  expect(response?.status()).toBe(404);
});
