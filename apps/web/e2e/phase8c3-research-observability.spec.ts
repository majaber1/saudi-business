import { expect, test, type Page } from "@playwright/test";

/**
 * Phase 8C.3 — Research Quality observability browser E2E.
 * Seeds deterministic quality via ALLOW_TEST_SEED=1 endpoint.
 */

const PASSWORD = "Phase8C3ObsTest9!";

async function registerAndOpenV2Workspace(page: Page) {
  const email = `phase8c3_${Date.now()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Switch language").click();
  await page.getByTestId("register-name").fill("Phase 8C.3 Observer");
  await page.getByTestId("register-email").fill(email);
  await page.getByTestId("register-password").fill(PASSWORD);
  await page.getByTestId("register-submit").click();
  await expect(page.getByTestId("projects-workspace")).toBeVisible({ timeout: 30000 });

  await page.getByTestId("add-project-btn").click();
  await page.getByTestId("project-name-input").fill("8C.3 Research Observability");
  await page.getByTestId("project-industry-select").selectOption("technology");
  await page.getByTestId("project-investment-input").fill("500000");
  await page.getByTestId("save-project-btn").click();
  await expect(page.getByTestId("project-workspace")).toBeVisible({ timeout: 30000 });

  await page.getByTestId("open-ai-study-workspace").click();
  await expect(page.getByTestId("v2-study-workspace")).toBeVisible({ timeout: 30000 });

  // Create a persisted study (URL must leave /studies/new/).
  const composer = page.locator("form input[type='text'], form textarea").first();
  await composer.fill(
    "Riyadh logistics SME studying Saudi CPI inflation and FDI investment climate for 2026.",
  );
  await page.getByRole("button", { name: /Send|إرسال/ }).click();
  await expect
    .poll(() => page.url(), { timeout: 120000 })
    .not.toMatch(/\/studies\/new(?:\/|$)/);
  await expect(page.getByTestId("v2-study-workspace")).toBeVisible({ timeout: 30000 });
  return email;
}

async function seedResearchQuality(page: Page) {
  const url = page.url();
  const match = url.match(/studies\/([^/?#]+)/);
  expect(match, `study id missing from url: ${url}`).toBeTruthy();
  const studyId = match![1];
  expect(studyId).not.toBe("new");

  const token = await page.evaluate(() => window.localStorage.getItem("sb_token"));
  expect(token, "auth token missing").toBeTruthy();

  const headers: Record<string, string> = {};
  if (token && token !== "session") {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await page.request.post(
    `/api/backend/api/v2/studies/${studyId}/test/seed-research-quality`,
    { headers },
  );
  expect(
    res.ok(),
    `seed failed status=${res.status()} body=${await res.text()}`,
  ).toBeTruthy();

  await page.reload();
  await expect(page.getByTestId("research-quality-observability")).toBeVisible({
    timeout: 30000,
  });
}

test("research quality observability renders, opens drawer, survives refresh, supports AR/EN", async ({
  page,
}, testInfo) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (/favicon/i.test(text)) return;
    consoleErrors.push(text);
  });

  await registerAndOpenV2Workspace(page);
  await seedResearchQuality(page);

  await expect(page.getByTestId("research-quality-summary")).toBeVisible();
  await expect(page.getByTestId("rq-metric-preferred")).toBeVisible();
  await expect(page.getByTestId("research-quality-claims")).toBeVisible();
  await expect(page.getByTestId("claim-quality-badge").first()).toBeVisible();

  await page.getByTestId("open-evidence-drawer").first().click();
  await expect(page.getByTestId("evidence-drawer")).toBeVisible();
  await expect(page.getByTestId("evidence-card").first()).toBeVisible();
  await expect(page.getByTestId("selection-reason").first()).toBeVisible();
  await expect(page.getByTestId("evidence-drawer")).toContainText(
    /GASTAT|Preferred|Current|Why this source|SAMA|Alternate/i,
  );
  await page.getByTestId("evidence-drawer-close").click();
  await expect(page.getByTestId("evidence-drawer")).toHaveCount(0);

  await page.reload();
  await expect(page.getByTestId("research-quality-observability")).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByTestId("claim-quality-badge").first()).toBeVisible();

  await page.getByLabel("Switch language").click();
  await expect(page.getByTestId("research-quality-summary")).toContainText(
    /صحة جودة البحث|مفضل/,
  );
  await page.getByTestId("open-evidence-drawer").first().click();
  await expect(page.getByTestId("evidence-drawer")).toContainText(
    /تفاصيل الدليل|لماذا هذا المصدر|رسمي/,
  );
  await page.screenshot({
    path: testInfo.outputPath("phase8c3-observability-ar.png"),
    fullPage: true,
  });
  await page.getByTestId("evidence-drawer-close").click();

  await page.getByLabel("Switch language").click();
  await expect(page.getByTestId("research-quality-summary")).toContainText(
    /Research quality health|Preferred/,
  );
  await page.screenshot({
    path: testInfo.outputPath("phase8c3-observability-en.png"),
    fullPage: true,
  });

  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});
