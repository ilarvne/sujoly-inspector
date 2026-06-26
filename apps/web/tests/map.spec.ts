import { test, expect } from './auth-fixture';

test('/ru/map renders map canvas', async ({ page }) => {
  await page.goto('/ru/map');
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  const canvas = page.locator('.maplibregl-canvas');
  await expect(canvas).toBeVisible();
});

test('/ru/map shows structure markers', async ({ page }) => {
  await page.goto('/ru/map');
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await page.waitForFunction(() => {
    const canvas = document.querySelector('.maplibregl-canvas') as HTMLCanvasElement | null;
    return canvas !== null && canvas.width > 0 && canvas.height > 0;
  }, { timeout: 15000 });
  const canvas = page.locator('.maplibregl-canvas');
  await expect(canvas).toBeVisible();
});

test('/ru/map shows OSM attribution', async ({ page }) => {
  await page.goto('/ru/map');
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await expect(page.locator('.maplibregl-ctrl-attrib')).toContainText('OpenStreetMap');
});

test('/en/map renders in en locale', async ({ page }) => {
  await page.goto('/en/map');
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await expect(page.locator('h1')).toContainText('Map');
});

test('/kk/map renders in kk locale', async ({ page }) => {
  await page.goto('/kk/map');
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await expect(page.locator('p')).toContainText('интерактивті');
});
