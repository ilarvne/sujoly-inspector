import { test, expect } from './auth-fixture';

test('/ru/dashboard renders dashboard title', async ({ page }) => {
  await page.goto('/ru/dashboard');
  await expect(page.locator('h1')).toContainText('Панель управления');
});

test('/ru/dashboard shows condition distribution chart', async ({ page }) => {
  await page.goto('/ru/dashboard');
  await page.waitForSelector('svg[role="application"]', { state: 'visible', timeout: 15000 });
  const card = page.locator('[data-slot="card"]').filter({ hasText: 'Распределение по состоянию' });
  await expect(card).toBeVisible();
  await expect(card.locator('svg[role="application"]')).toBeVisible();
});

test('/ru/dashboard shows repair queue', async ({ page }) => {
  await page.goto('/ru/dashboard');
  await page.waitForSelector('svg[role="application"]', { state: 'visible', timeout: 15000 });
  const card = page.locator('[data-slot="card"]').filter({ hasText: 'Очередь ремонта' });
  await expect(card).toBeVisible();
  await expect(card).toContainText('Тасуткель');
});

test('/ru/dashboard shows inspection stats', async ({ page }) => {
  await page.goto('/ru/dashboard');
  await page.waitForSelector('svg[role="application"]', { state: 'visible', timeout: 15000 });
  const card = page.locator('[data-slot="card"]').filter({ hasText: 'Охват инспекциями' });
  await expect(card).toBeVisible();
  await expect(card).toContainText('55');
});

test('/ru/dashboard shows geographic distribution', async ({ page }) => {
  await page.goto('/ru/dashboard');
  await page.waitForSelector('svg[role="application"]', { state: 'visible', timeout: 15000 });
  const card = page
    .locator('[data-slot="card"]')
    .filter({ hasText: 'Географическая тепловая карта' });
  await expect(card).toBeVisible();
  await expect(card.locator('svg[role="application"]')).toBeVisible();
});

test('/en/dashboard renders in English', async ({ page }) => {
  await page.goto('/en/dashboard');
  await page.waitForSelector('svg[role="application"]', { state: 'visible', timeout: 15000 });
  await expect(page.locator('h1')).toContainText('Dashboard');
  await expect(page.getByText('Condition Distribution').first()).toBeVisible();
  await expect(page.getByText('Repair Queue').first()).toBeVisible();
});
