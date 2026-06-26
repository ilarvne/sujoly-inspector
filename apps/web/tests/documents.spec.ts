import { test, expect } from './auth-fixture';
import type { Page } from '@playwright/test';

async function waitForMapReady(page: Page) {
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await page.waitForFunction(() => {
    const canvas = document.querySelector('.maplibregl-canvas') as HTMLCanvasElement | null;
    return canvas !== null && canvas.width > 0 && canvas.height > 0;
  }, { timeout: 15000 });
  await page.waitForFunction(() => !!(window as Window & { __maplibreMap?: unknown }).__maplibreMap, { timeout: 15000 });
  await page.waitForTimeout(1000);
}

async function clickStructureAt(page: Page, lng: number, lat: number) {
  const point = await page.evaluate(({ lng, lat }) => {
    const map = (window as Window & { __maplibreMap?: { project: (ll: { lng: number; lat: number }) => { x: number; y: number } } }).__maplibreMap;
    if (!map) return null;
    const container = document.querySelector('.maplibregl-map') as HTMLElement;
    if (!container) return null;
    const rect = container.getBoundingClientRect();
    const pixel = map.project({ lng, lat });
    return { x: rect.left + pixel.x, y: rect.top + pixel.y };
  }, { lng, lat });

  if (!point) return false;
  await page.mouse.click(point.x, point.y);
  return true;
}

async function openPassport(page: Page) {
  const structures = [
    { lng: 72.80, lat: 43.10 },
    { lng: 72.40, lat: 43.20 },
    { lng: 72.10, lat: 43.50 },
    { lng: 71.80, lat: 43.20 },
    { lng: 71.35, lat: 42.95 },
    { lng: 73.25, lat: 42.75 },
  ];

  for (const { lng, lat } of structures) {
    const clicked = await clickStructureAt(page, lng, lat);
    if (!clicked) continue;
    try {
      await page.waitForSelector('[data-slot="sheet-content"]', { timeout: 3000 });
      return true;
    } catch {
      // Try next structure coordinate
    }
  }
  return false;
}

test('Documents tab shows upload area', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Документы' }).click();

  await expect(page.locator('[data-testid="document-upload-area"]')).toBeVisible({ timeout: 5000 });
});

test('Documents tab works in English', async ({ page }) => {
  await page.goto('/en/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Documents' }).click();

  await expect(page.locator('[data-testid="document-upload-area"]')).toBeVisible({ timeout: 5000 });
});
