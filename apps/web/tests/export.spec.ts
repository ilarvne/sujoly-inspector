import { test, expect } from './auth-fixture';

test('Reports page renders export panel', async ({ page }) => {
  await page.goto('/ru/reports');

  await expect(page.locator('h1')).toContainText('Отчёты');
  await expect(page.getByTestId('export-csv')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('export-geojson')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('export-pdf')).toBeVisible({ timeout: 10000 });
});

test('PDF export button disabled until structure selected', async ({ page }) => {
  await page.goto('/ru/reports');

  const pdfButton = page.getByTestId('export-pdf');
  await expect(pdfButton).toBeVisible();
  await expect(pdfButton).toBeDisabled();

  const structureTrigger = page.locator('[data-slot="select-trigger"]');
  await structureTrigger.click();
  await page.getByRole('option', { name: 'KZ-ZH-0001' }).click();

  await expect(pdfButton).toBeEnabled({ timeout: 10000 });
});

test('CSV export triggers download', async ({ page }) => {
  await page.goto('/ru/reports');

  const csvButton = page.getByTestId('export-csv');
  await expect(csvButton).toBeEnabled({ timeout: 10000 });

  const downloadPromise = page.waitForEvent('download');
  await csvButton.click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('.csv');
});

test('GeoJSON export triggers download', async ({ page }) => {
  await page.goto('/ru/reports');

  const geojsonButton = page.getByTestId('export-geojson');
  await expect(geojsonButton).toBeEnabled({ timeout: 10000 });

  const downloadPromise = page.waitForEvent('download');
  await geojsonButton.click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('.geojson');
});

test('Reports page works in English', async ({ page }) => {
  await page.goto('/en/reports');

  await expect(page.locator('h1')).toContainText('Reports');
  await expect(page.getByTestId('export-csv')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('export-geojson')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('export-pdf')).toBeVisible({ timeout: 10000 });
});
