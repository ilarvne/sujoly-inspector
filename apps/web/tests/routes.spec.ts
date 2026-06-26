import { test, expect } from './auth-fixture';

const routes = ['', '/dashboard', '/map', '/objects', '/copilot', '/reports', '/hydrofinder', '/login'];
const locales = ['ru', 'kk', 'en'];

for (const locale of locales) {
  for (const route of routes) {
    test(`${locale}${route || '/'} returns 200`, async ({ page }) => {
      const response = await page.goto(`/${locale}${route}`);
      expect(response?.status()).toBe(200);
    });
  }
}
