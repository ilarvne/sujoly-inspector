import { test, expect, type Page } from '@playwright/test';

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

async function setEngineerAuth(page: Page) {
  await page.evaluate(() => {
    localStorage.setItem('sujoly-auth', JSON.stringify({
      state: { user: { id: 'u-engineer', name: 'Engineer', role: 'engineer' } },
      version: 0,
    }));
  });
}

test('Passport has 4 tabs after clicking structure', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toBeVisible();

  await expect(page.getByRole('tab', { name: 'Обзор' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Осмотры' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Риск' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Документы' })).toBeVisible();
});

test('Inspections tab shows timeline', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Осмотры' }).click();

  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toContainText('Инспектор', { timeout: 5000 });
});

test('Risk tab shows score and components', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Риск' }).click();

  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toContainText('Общий балл риска', { timeout: 5000 });
  await expect(sheet).toContainText('Конструктивная целостность');
});

test('Override button hidden without login, visible for engineer', async ({ page }) => {
  await page.goto('/ru/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Риск' }).click();
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toContainText('Общий балл риска', { timeout: 5000 });

  const overrideButton = page.getByRole('button', { name: 'Инженерное решение' });
  await expect(overrideButton).not.toBeVisible({ timeout: 3000 });

  await setEngineerAuth(page);
  await page.reload();
  await waitForMapReady(page);
  const opened2 = await openPassport(page);
  expect(opened2, 'Passport panel did not open after auth setup').toBe(true);

  await page.getByRole('tab', { name: 'Риск' }).click();
  await expect(sheet).toContainText('Общий балл риска', { timeout: 5000 });

  const overrideButton2 = page.getByRole('button', { name: 'Инженерное решение' });
  await expect(overrideButton2).toBeVisible({ timeout: 5000 });
});

test('Override dialog opens with form', async ({ page }) => {
  await page.goto('/ru/map');
  await setEngineerAuth(page);
  await page.reload();
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Риск' }).click();
  const overrideButton = page.getByRole('button', { name: 'Инженерное решение' });
  await expect(overrideButton).toBeVisible({ timeout: 5000 });
  await overrideButton.click();

  const dialog = page.locator('[data-slot="dialog-content"]');
  await expect(dialog).toBeVisible({ timeout: 3000 });

  await expect(dialog.locator('[data-slot="select-trigger"]')).toBeVisible();
  await expect(dialog.locator('[data-slot="textarea"]')).toBeVisible();
  await expect(dialog).toContainText('История изменений');
});

test('Inspection and risk tabs work in English', async ({ page }) => {
  await page.goto('/en/map');
  await waitForMapReady(page);
  const opened = await openPassport(page);
  expect(opened, 'Passport panel did not open after clicking structure markers').toBe(true);

  await page.getByRole('tab', { name: 'Inspections' }).click();
  const sheet = page.locator('[data-slot="sheet-content"]');
  await expect(sheet).toContainText('Inspector', { timeout: 5000 });

  await page.getByRole('tab', { name: 'Risk' }).click();
  await expect(sheet).toContainText('Overall Risk Score', { timeout: 5000 });
});
