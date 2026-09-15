import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "Phase9Test9!";

async function registerAndLogin(page: Page, email: string) {
  await page.goto("/register");
  await page.getByTestId("register-name").fill("Phase 9 Tester");
  await page.getByTestId("register-email").fill(email);
  await page.getByTestId("register-password").fill(PASSWORD);
  await page.getByTestId("register-submit").click();
  await expect(page.getByTestId("projects-workspace")).toBeVisible({ timeout: 30000 });
}

async function createProjectAndStudy(page: Page) {
  await page.getByTestId("add-project-btn").click();
  await page.getByTestId("project-name-input").fill("Tabea AI CRM");
  await page.getByTestId("project-industry-select").selectOption("technology");
  await page.getByTestId("project-investment-input").fill("350000");
  await page.getByTestId("save-project-btn").click();
  await expect(page.getByTestId("project-workspace")).toBeVisible({ timeout: 30000 });
  await expect(page.getByTestId("project-workspace-title")).toContainText("Tabea AI CRM");

  await page.getByTestId("start-study-btn").click();
  await expect(page.getByTestId("study-workspace")).toBeVisible({ timeout: 30000 });
}

async function navigateStudySections(page: Page) {
  await page.getByTestId("study-section-profile").click();
  await page.getByTestId("profile-activity-input").fill("B2B SaaS AI CRM & Sales Automation");
  await page.getByTestId("save-business-profile").click();
  await expect(page.getByText(/Saved|تم الحفظ/)).toBeVisible();

  await page.getByTestId("study-section-assumptions").click();
  await page.getByTestId("add-assumption-btn").click();
  await page.getByTestId("assumption-key-input").fill("capex");
  await page.getByTestId("assumption-label-en").fill("CAPEX");
  await page.getByTestId("assumption-label-ar").fill("النفقات الرأسمالية");
  await page.getByTestId("assumption-value-input").fill("350000");
  await page.getByTestId("assumption-origin-select").selectOption("USER");
  await page.getByTestId("save-assumption-btn").click();
  await expect(page.getByTestId("assumption-card-capex")).toBeVisible();

  await page.getByTestId("study-section-financial").click();
  await expect(page.getByTestId("financial-analysis-workspace")).toBeVisible();

  await page.getByTestId("study-section-validation").click();
  await expect(page.getByTestId("validation-os-workspace")).toBeVisible({ timeout: 30000 });
}

async function verifyNavAndLayout(page: Page, testInfo: any, label: string) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: testInfo.outputPath(`${label}-home.png`), fullPage: true });

  const nav = page.locator("nav, [role=navigation]").first();
  await expect(nav).toBeVisible();

  const logo = page.getByText("Saudi Business").first();
  const logoAr = page.getByText("المنصة السعودية للأعمال").first();
  const hasLogo = await logo.isVisible().catch(() => false) || await logoAr.isVisible().catch(() => false);
  expect(hasLogo).toBeTruthy();
}

test.describe("Phase 9 — multi-viewport smoke", () => {
  test("English desktop: navigation and study creation", async ({ page }, testInfo) => {
    const email = `en_desk_${Date.now()}@example.com`;
    await page.goto("/register");
    const langBtn = page.getByLabel("Switch language");
    const text = await langBtn.textContent();
    if (!text?.includes("العربية")) await langBtn.click();

    await registerAndLogin(page, email);
    await createProjectAndStudy(page);
    await navigateStudySections(page);
    await page.screenshot({ path: testInfo.outputPath("en-desktop-study.png"), fullPage: true });
  });

  test("Arabic desktop: navigation and layout", async ({ page }, testInfo) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const html = page.locator("html");
    const dir = await html.getAttribute("dir");
    const lang = await html.getAttribute("lang");

    await page.screenshot({ path: testInfo.outputPath("ar-desktop-home.png"), fullPage: true });

    const nav = page.locator("nav").first();
    await expect(nav).toBeVisible();
  });

  test("Mobile viewport: responsive layout", async ({ browser }, testInfo) => {
    const context = await browser.newContext({
      viewport: { width: 375, height: 812 },
      isMobile: true,
    });
    const page = await context.newPage();

    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: testInfo.outputPath("mobile-home.png"), fullPage: true });

    const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(pageWidth).toBeLessThanOrEqual(400);

    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: testInfo.outputPath("mobile-login.png"), fullPage: true });

    await page.goto("/register");
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: testInfo.outputPath("mobile-register.png"), fullPage: true });

    const registerPageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(registerPageWidth).toBeLessThanOrEqual(400);

    await context.close();
  });
});
