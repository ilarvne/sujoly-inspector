import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/ru');
  await page.evaluate(() => localStorage.clear());
});

test('Login page renders with 4 role cards', async ({ page }) => {
  await page.goto('/ru/login');
  await expect(page.locator('h1')).toContainText('Вход в систему');
  await expect(page.locator('[data-testid="role-card-admin"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-engineer"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-inspector"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-viewer"]')).toBeVisible();
  await expect(page.locator('[data-testid="signin-button"]')).toBeDisabled();
});

test('Selecting a role enables sign-in', async ({ page }) => {
  await page.goto('/ru/login');
  await page.locator('[data-testid="role-card-engineer"]').click();
  await expect(page.locator('[data-testid="signin-button"]')).toBeEnabled();
});

test('Sign in navigates to /map', async ({ page }) => {
  await page.goto('/ru/login');
  await page.locator('[data-testid="role-card-admin"]').click();
  await page.locator('[data-testid="signin-button"]').click();
  await expect(page).toHaveURL(/\/ru\/map/);
  await expect(page.locator('[data-testid="user-menu-trigger"]')).toBeVisible();
});

test('User menu shows user name and logout', async ({ page }) => {
  await page.goto('/ru/login');
  await page.locator('[data-testid="role-card-engineer"]').click();
  await page.locator('[data-testid="signin-button"]').click();
  await expect(page).toHaveURL(/\/ru\/map/);
  await expect(page.locator('[data-testid="user-menu-trigger"]')).toBeVisible();
  await page.locator('[data-testid="user-menu-trigger"]').click();
  await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
});

test('Logout navigates to login', async ({ page }) => {
  await page.goto('/ru/login');
  await page.locator('[data-testid="role-card-engineer"]').click();
  await page.locator('[data-testid="signin-button"]').click();
  await expect(page).toHaveURL(/\/ru\/map/);
  await page.locator('[data-testid="user-menu-trigger"]').click();
  await page.locator('[data-testid="logout-button"]').click();
  await expect(page).toHaveURL(/\/ru\/login/);
});

test('Auth persists across navigation', async ({ page }) => {
  await page.goto('/ru/login');
  await page.locator('[data-testid="role-card-engineer"]').click();
  await page.locator('[data-testid="signin-button"]').click();
  await expect(page).toHaveURL(/\/ru\/map/);
  await expect(page.locator('[data-testid="user-menu-trigger"]')).toBeVisible();
  await page.goto('/ru/dashboard');
  await expect(page.locator('[data-testid="user-menu-trigger"]')).toBeVisible();
});

test('Login page works in English', async ({ page }) => {
  await page.goto('/en/login');
  await expect(page.locator('h1')).toContainText('Sign In');
  await expect(page.locator('[data-testid="role-card-admin"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-engineer"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-inspector"]')).toBeVisible();
  await expect(page.locator('[data-testid="role-card-viewer"]')).toBeVisible();
});

test('Not logged in redirects to login', async ({ page }) => {
  await page.goto('/ru');
  await page.evaluate(() => localStorage.clear());
  await page.goto('/ru/map');
  await expect(page).toHaveURL(/\/ru\/login/);
});
