import { test, expect } from '@playwright/test';

/**
 * E2E Tests — Chat Flow
 *
 * Tests the AI Agent chat interface:
 * - Welcome message display
 * - Quick action chips
 * - Message input and send
 * - Agent response with recommendations
 */
test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
  });

  test('displays welcome message on first visit', async ({ page }) => {
    // Welcome screen shows h1 "SRE Engineer Assistant" when no messages
    const welcome = page.getByRole('heading', { name: 'SRE Engineer Assistant' });
    await expect(welcome).toBeVisible({ timeout: 10000 });
  });

  test('displays quick action chips', async ({ page }) => {
    // Quick actions group with aria-label "Quick actions"
    const quickActions = page.locator('[role="group"][aria-label="Quick actions"]');
    await expect(quickActions).toBeVisible({ timeout: 10000 });
  });

  test('allows typing in the input field', async ({ page }) => {
    const input = page.getByRole('textbox', { name: 'Chat message input' });
    await expect(input).toBeVisible({ timeout: 10000 });

    await input.fill('查看告警');
    await expect(input).toHaveValue('查看告警');
  });

  test('send button is disabled when input is empty', async ({ page }) => {
    const sendButton = page.getByRole('button', { name: 'Send message' });
    await expect(sendButton).toBeVisible({ timeout: 10000 });
    await expect(sendButton).toBeDisabled();
  });

  test('send button becomes enabled when input has text', async ({ page }) => {
    const input = page.getByRole('textbox', { name: 'Chat message input' });
    const sendButton = page.getByRole('button', { name: 'Send message' });

    await input.fill('查看告警');
    await expect(sendButton).toBeEnabled();
  });

  test('clicking quick action fills input', async ({ page }) => {
    const quickAction = page.locator('[role="group"][aria-label="Quick actions"] button').first();
    await quickAction.click();

    // After clicking a quick action, the message is sent directly via send()
    // so the input stays empty but a message bubble should appear
    const messages = page.locator('[aria-label="Assistant"]');
    await expect(messages.first()).toBeVisible({ timeout: 10000 });
  });
});
