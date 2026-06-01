import { defineConfig, devices } from '@playwright/test';

/**
 * V3.1 SRE Platform — Playwright E2E Test Configuration
 *
 * Tests run against the dev servers:
 * - Backend: http://localhost:8688
 * - Frontend: http://localhost:5173
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: true,
  retries: 1,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  /* Start backend and frontend before running tests */
  webServer: [
    {
      command: 'cd ../../backend && python -m uvicorn app.main:app --port 8688',
      port: 8688,
      reuseExistingServer: true,
      timeout: 30000,
    },
    {
      command: 'cd ../../frontend && npm run dev -- --port 3000',
      port: 3000,
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
});
