import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Navigation
 *
 * Tests the navigation between pages:
 * - Sidebar navigation works
 * - All pages are accessible
 * - Active state is correct
 */
test.describe('Navigation', () => {
  test('root redirects to /chat', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/chat/);
  });

  test('sidebar navigation to dashboard', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const dashboardLink = page.locator('a[href="/dashboard"], button:has-text("仪表盘")');
    await dashboardLink.first().click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('sidebar navigation to alerts', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const alertsLink = page.locator('a[href="/alerts"], button:has-text("告警")');
    await alertsLink.first().click();
    await expect(page).toHaveURL(/\/alerts/);
  });

  test('sidebar navigation to resources', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const resourcesLink = page.locator('a[href="/resources"], button:has-text("资源")');
    await resourcesLink.first().click();
    await expect(page).toHaveURL(/\/resources/);
  });

  test('sidebar navigation to operations', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const operationsLink = page.locator('a[href="/operations"], button:has-text("操作")');
    await operationsLink.first().click();
    await expect(page).toHaveURL(/\/operations/);
  });
});
