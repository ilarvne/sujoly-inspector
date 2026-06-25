import { test, expect, type Page } from '@playwright/test';

async function waitForMap(page: Page) {
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
}

test('Filter panel is visible on map page', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMap(page);

  const filterPanel = page.getByTestId('filter-panel');
  await expect(filterPanel).toBeVisible();
  await expect(filterPanel).toContainText('Фильтры');
});

test('Selecting condition filter updates UI', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMap(page);

  const filterPanel = page.getByTestId('filter-panel');
  const conditionTrigger = page.getByRole('combobox', { name: 'Состояние' });

  await conditionTrigger.click();
  await page.getByRole('option', { name: 'Критическое' }).click();

  await expect(conditionTrigger).toContainText('Критическое');
  const badge = filterPanel.locator('[data-slot="badge"]');
  await expect(badge).toBeVisible();
  await expect(badge).toContainText('1');
});

test('Reset button clears filters', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMap(page);

  const filterPanel = page.getByTestId('filter-panel');
  const conditionTrigger = page.getByRole('combobox', { name: 'Состояние' });

  await conditionTrigger.click();
  await page.getByRole('option', { name: 'Критическое' }).click();
  await expect(conditionTrigger).toContainText('Критическое');

  await page.getByRole('button', { name: 'Сбросить' }).click();

  await expect(conditionTrigger).toContainText('Все');
  const badge = filterPanel.locator('[data-slot="badge"]');
  await expect(badge).not.toBeVisible();
});

test('Filter persists when navigating to dashboard and back', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMap(page);

  const conditionTrigger = page.getByRole('combobox', { name: 'Состояние' });
  await conditionTrigger.click();
  await page.getByRole('option', { name: 'Критическое' }).click();
  await expect(conditionTrigger).toContainText('Критическое');

  await page.getByRole('link', { name: 'Панель управления' }).click();
  await expect(page.locator('h1')).toContainText('Панель управления');

  await page.getByRole('link', { name: 'Карта' }).click();
  await waitForMap(page);

  const filterPanel = page.getByTestId('filter-panel');
  await expect(filterPanel).toBeVisible();
  await expect(
    page.getByRole('combobox', { name: 'Состояние' })
  ).toContainText('Критическое');
  const badge = filterPanel.locator('[data-slot="badge"]');
  await expect(badge).toBeVisible();
});

test('Filter works in English locale', async ({ page }) => {
  await page.goto('/en/map');
  await waitForMap(page);

  const filterPanel = page.getByTestId('filter-panel');
  await expect(filterPanel).toContainText('Filters');

  const conditionTrigger = page.getByRole('combobox', { name: 'Condition' });
  await conditionTrigger.click();
  await page.getByRole('option', { name: 'Critical' }).click();

  await expect(conditionTrigger).toContainText('Critical');
});
