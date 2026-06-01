import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Resources
 *
 * Tests the resources page:
 * - Page loads correctly
 * - Asset type tabs are displayed
 * - Resource list is rendered
 */
test.describe('Resources', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/resources');
    await page.waitForLoadState('networkidle');
  });

  test('resources page loads', async ({ page }) => {
    // ResourcesView shows h1 "Resources"
    const heading = page.getByRole('heading', { name: 'Resources' });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('asset type tabs are displayed', async ({ page }) => {
    // Tabs component renders tab buttons for VM/Physical/Storage
    const tabs = page.locator('button').filter({ hasText: /VM|Physical|Storage|All/ });
    await expect(tabs.first()).toBeVisible({ timeout: 10000 });
  });

  test('resource list or empty state is displayed', async ({ page }) => {
    // Should show either resource table or empty state
    const content = page.locator('[class*="rounded-lg"]').filter({ hasText: /resource|资源|No resources|暂无/ });
    await expect(content.first()).toBeVisible({ timeout: 10000 });
  });
});
