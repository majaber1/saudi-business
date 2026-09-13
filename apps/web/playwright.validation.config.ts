import { defineConfig, devices } from "@playwright/test";

/**
 * Validation-only Playwright config: uses already-running local servers.
 * Does not start its own webServer (avoids wiping the live validation DB/session).
 */
export default defineConfig({
  testDir: "../../docs/validation",
  testMatch: /product_validation_sprint\.spec\.ts/,
  timeout: 420000,
  expect: { timeout: 30000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3000",
    screenshot: "off",
    trace: "off",
    video: "off",
    headless: true,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
