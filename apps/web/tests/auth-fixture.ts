import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      localStorage.setItem('sujoly-auth', JSON.stringify({
        state: { user: { id: 'u-admin', name: 'Administrator', role: 'admin' } },
        version: 0,
      }));
    });
    await use(page);
  },
});

export { expect };
