import { test, expect } from './auth-fixture';

test('Kazakh-specific characters are present on KK page', async ({ page }) => {
  await page.goto('/kk');
  await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 });
  const bodyText = await page.locator('body').innerText();
  const kazakhChars = ['ә', 'ғ', 'қ', 'ң', 'ө', 'ұ', 'ү', 'һ', 'і'];
  for (const char of kazakhChars) {
    expect(bodyText).toContain(char);
  }
});

test('headings use Manrope font (display)', async ({ page }) => {
  await page.goto('/ru');
  const h1FontFamily = await page.locator('h1').evaluate(
    (el) => getComputedStyle(el).fontFamily
  );
  expect(h1FontFamily.toLowerCase()).toMatch(/manrope/);
});

test('body text uses Inter font (sans)', async ({ page }) => {
  await page.goto('/ru');
  const bodyFontFamily = await page.locator('body').evaluate(
    (el) => getComputedStyle(el).fontFamily
  );
  expect(bodyFontFamily.toLowerCase()).toMatch(/inter/);
});
