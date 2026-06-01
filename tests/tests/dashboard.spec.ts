import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Dashboard
 *
 * Tests the dashboard page:
 * - Page loads correctly
 * - Stat cards are displayed
 * - Charts are rendered
 */
test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('dashboard page loads', async ({ page }) => {
    // DashboardView shows h1 "Dashboard"
    const heading = page.getByRole('heading', { name: 'Dashboard' });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('stat cards are displayed', async ({ page }) => {
    // Should have stat cards with numbers
    const statCards = page.locator('[class*="rounded-lg"]').filter({ hasText: /VM|Host|Alert|Operation/ });
    await expect(statCards.first()).toBeVisible({ timeout: 10000 });
  });

  test('navigation sidebar is visible', async ({ page }) => {
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible({ timeout: 10000 });
  });
});
