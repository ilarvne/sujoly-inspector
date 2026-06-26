import { test, expect, type Page } from '@playwright/test';

async function waitForMapReady(page: Page) {
  await page.waitForSelector('.maplibregl-canvas', { timeout: 15000 });
  await page.waitForFunction(() => {
    const canvas = document.querySelector('.maplibregl-canvas') as HTMLCanvasElement | null;
    return canvas !== null && canvas.width > 0 && canvas.height > 0;
  }, { timeout: 15000 });
  await page.waitForTimeout(2000);
}

async function clickStructureAt(page: Page, lng: number, lat: number) {
  const point = await page.evaluate(({ lng, lat }) => {
    const canvas = document.querySelector('.maplibregl-canvas') as HTMLCanvasElement;
    const rect = canvas.getBoundingClientRect();

    const centerLng = 72.6;
    const centerLat = 44.0;
    const zoom = 7;
    const worldSize = 256 * Math.pow(2, zoom);

    const project = (l: number, la: number) => {
      const x = (l + 180) / 360 * worldSize;
      const latRad = la * Math.PI / 180;
      const y = (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * worldSize;
      return { x, y };
    };

    const center = project(centerLng, centerLat);
    const target = project(lng, lat);

    const canvasX = rect.width / 2 + (target.x - center.x);
    const canvasY = rect.height / 2 + (target.y - center.y);

    return {
      x: rect.left + canvasX,
      y: rect.top + canvasY,
    };
  }, { lng, lat });

  await page.mouse.click(point.x, point.y);
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
    await clickStructureAt(page, lng, lat);
    try {
      await page.waitForSelector('[data-slot="sheet-content"]', { timeout: 3000 });
      return true;
    } catch {
      // Try next structure coordinate
    }
  }
  return false;
}

test('Click structure opens passport panel', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toBeVisible();
  await expect(sheet).toContainText('Идентификация');
});

test('Passport shows provenance section', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toBeVisible();
  await expect(sheet).toContainText('Происхождение данных');
});

test('Passport closes on overlay click', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toBeVisible();
  await page.locator('[data-slot="sheet-overlay"]').click();
  await expect(sheet).not.toBeVisible();
});

test('Passport works in English locale', async ({ page }) => {
  await page.goto('/en/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toBeVisible();
  await expect(sheet).toContainText('Identity');
});
