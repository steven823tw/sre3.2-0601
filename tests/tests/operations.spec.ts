import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Operations
 *
 * Tests the operations page:
 * - Page loads correctly
 * - Status tabs are displayed
 * - Operation list is rendered
 */
test.describe('Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/operations');
    await page.waitForLoadState('networkidle');
  });

  test('operations page loads', async ({ page }) => {
    // OperationsView shows h1 "Operations"
    const heading = page.getByRole('heading', { name: 'Operations' });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('status tabs are displayed', async ({ page }) => {
    // Tabs component renders tab buttons
    const tabs = page.locator('button').filter({ hasText: /All|Pending|Running|Completed|Failed/ });
    await expect(tabs.first()).toBeVisible({ timeout: 10000 });
  });

  test('operation list or empty state is displayed', async ({ page }) => {
    // Should show either operation cards, empty state, or the page content area
    const content = page.locator('main, [class*="space-y"], [class*="flex-1"]').filter({ hasText: /Operation|操作|No operations|暂无|Pending|Running|Completed/ });
    await expect(content.first()).toBeVisible({ timeout: 10000 });
  });
});
