import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Alerts
 *
 * Tests the alerts page:
 * - Page loads correctly
 * - Severity tabs are displayed
 * - Alert cards or empty state is rendered
 */
test.describe('Alerts', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/alerts');
    await page.waitForLoadState('networkidle');
  });

  test('alerts page loads', async ({ page }) => {
    // AlertsView shows h1 "Alerts"
    const heading = page.getByRole('heading', { name: 'Alerts' });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('severity tabs are displayed', async ({ page }) => {
    // Tabs component renders tab buttons
    const tabs = page.locator('button').filter({ hasText: /All|P0|P1|P2|P3|P4/ });
    await expect(tabs.first()).toBeVisible({ timeout: 10000 });
  });

  test('alert list or empty state is displayed', async ({ page }) => {
    // Should show either alert cards or empty state
    const content = page.locator('[class*="rounded-lg"]').filter({ hasText: /alert|告警|No alerts|暂无/ });
    await expect(content.first()).toBeVisible({ timeout: 10000 });
  });
});
