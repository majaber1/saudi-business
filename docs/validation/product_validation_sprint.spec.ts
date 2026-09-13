/**
 * Product Validation Sprint — browser driver (docs/validation artifact only).
 * Targets already-running local servers. Does not modify application code.
 *
 * Exercises real V2 study workflow for three business scenarios:
 * SME coffee (Riyadh), industrial recycling (Jeddah), digital SaaS (KSA).
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "fs";
import path from "path";

const OUT = "/opt/cursor/artifacts/product-validation";
const PASSWORD = "ValidationSprint9!";

type CaseSpec = {
  id: string;
  name: string;
  industry: string;
  investment: string;
  archetypeId: string;
  briefing: string;
};

const CASES: CaseSpec[] = [
  {
    id: "case1-sme",
    name: "Riyadh Specialty Coffee Shop",
    industry: "food",
    investment: "450000",
    archetypeId: "services",
    briefing:
      "Specialty coffee shop (قهوة مختصة) in Riyadh for young professionals. Sit-in and takeaway. Need Saudi/Riyadh F&B market size, competitors, cup pricing, rent and labor assumptions, and financial feasibility for a 450,000 SAR budget.",
  },
  {
    id: "case2-industrial",
    name: "Jeddah Plastic Recycling Plant",
    industry: "industrial",
    investment: "3500000",
    archetypeId: "industrial",
    briefing:
      "Small plastic recycling and pelletizing plant in Jeddah industrial area. Collects PET/HDPE waste, produces recycled pellets for local manufacturers. Need supply chain, capex, Saudi regulations, demand, and operational risks.",
  },
  {
    id: "case3-digital",
    name: "SME Accounting SaaS KSA",
    industry: "technology",
    investment: "800000",
    archetypeId: "saas_digital",
    briefing:
      "B2B SaaS accounting and invoicing app for Saudi micro/small businesses with ZATCA e-invoicing readiness. Need market size, competitors, pricing/CAC assumptions, scalability, and go/no-go recommendation. Budget 800,000 SAR.",
  },
];

function ensureOut() {
  fs.mkdirSync(OUT, { recursive: true });
}

async function shot(page: Page, name: string) {
  ensureOut();
  const file = path.join(OUT, name);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function ensureEnglish(page: Page) {
  for (let i = 0; i < 4; i++) {
    const englishCue = await page
      .getByText(/My projects|Add project|Study Workspace|Create account|Sign in|Projects|Register/i)
      .first()
      .isVisible()
      .catch(() => false);
    if (englishCue) return;
    const toggle = page.getByLabel("Switch language");
    if (await toggle.count()) await toggle.click();
    await page.waitForTimeout(400);
  }
}

async function registerUser(page: Page, tag: string) {
  const email = `validation_${tag}_${Date.now()}@example.com`;
  await page.goto("/register");
  await ensureEnglish(page);
  // Register page often defaults to Arabic — force one language toggle if still Arabic labels.
  const nameField = page.getByTestId("register-name");
  await expect(nameField).toBeVisible({ timeout: 30000 });
  if (await page.getByText(/إنشاء حساب|الاسم/i).first().isVisible().catch(() => false)) {
    await page.getByLabel("Switch language").click();
    await page.waitForTimeout(400);
  }
  await nameField.fill(`Validation ${tag}`);
  await page.getByTestId("register-email").fill(email);
  await page.getByTestId("register-password").fill(PASSWORD);
  await page.getByTestId("register-submit").click();
  await expect(page.getByTestId("projects-workspace")).toBeVisible({ timeout: 60000 });
  await ensureEnglish(page);
  return email;
}

async function createProject(page: Page, spec: CaseSpec) {
  await page.getByTestId("add-project-btn").click();
  await page.getByTestId("project-name-input").fill(spec.name);
  await page.getByTestId("project-industry-select").selectOption(spec.industry);
  await page.getByTestId("project-investment-input").fill(spec.investment);
  if (await page.getByTestId("project-stage-select").count()) {
    await page.getByTestId("project-stage-select").selectOption("idea");
  }
  await page.getByTestId("save-project-btn").click();
  await expect(page.getByTestId("project-workspace")).toBeVisible({ timeout: 60000 });
}

async function openStudy(page: Page, briefing: string) {
  await page.getByTestId("open-ai-study-workspace").click();
  await expect(page.getByTestId("v2-study-workspace")).toBeVisible({ timeout: 60000 });
  const composer = page.locator("form input[type='text'], form textarea").first();
  await composer.fill(briefing);
  await page.getByRole("button", { name: /Send|إرسال/ }).click();
  await expect.poll(() => page.url(), { timeout: 180000 }).not.toMatch(/\/studies\/new(?:\/|$)/);
  await expect(page.getByTestId("v2-study-workspace")).toBeVisible({ timeout: 60000 });
  // Allow initial research / classification to settle.
  await page.waitForTimeout(8000);
}

async function fetchStudyPayload(page: Page) {
  const url = page.url();
  const match = url.match(/studies\/([^/?#]+)/);
  if (!match || match[1] === "new") return null;
  const studyId = match[1];
  return page.evaluate(async (id) => {
    const res = await fetch(`/api/backend/api/v2/studies/${id}`, {
      credentials: "same-origin",
      headers: { accept: "application/json" },
    });
    const text = await res.text();
    let json: unknown = null;
    try {
      json = JSON.parse(text);
    } catch {
      json = { raw: text.slice(0, 2000) };
    }
    return { ok: res.ok, status: res.status, studyId: id, body: json };
  }, studyId);
}

async function progress(page: Page, archetypeId: string) {
  const actions: string[] = [];
  const phasesSeen = new Set<string>();

  for (let round = 0; round < 14; round++) {
    const phaseText = ((await page.getByTestId("study-phase").textContent().catch(() => "")) || "").trim();
    if (phaseText) phasesSeen.add(phaseText);

    if (await page.getByTestId("archetype-classification-panel").isVisible().catch(() => false)) {
      const opt = page.getByTestId(`archetype-option-${archetypeId}`);
      if (await opt.count()) await opt.click();
      else {
        const first = page.locator('[data-testid^="archetype-option-"]').first();
        if (await first.count()) await first.click();
      }
      const conf = page.getByTestId("confirm-archetype-btn");
      if (await conf.isEnabled().catch(() => false)) {
        await conf.click();
        actions.push(`archetype@${round}`);
        await page.waitForTimeout(5000);
      }
    }

    if (await page.getByTestId("discovery-questions-panel").isVisible().catch(() => false)) {
      for (let q = 0; q < 20; q++) {
        const estimate = page.getByTestId("discovery-let-ai-estimate");
        if (await estimate.isVisible().catch(() => false)) {
          await estimate.click();
          await page.waitForTimeout(500);
        }
        const next = page.getByTestId("discovery-next");
        if (await next.isVisible().catch(() => false) && (await next.isEnabled().catch(() => false))) {
          await next.click();
          await page.waitForTimeout(400);
          continue;
        }
        break;
      }
      const submit = page
        .getByTestId("discovery-questions-submit")
        .or(page.getByTestId("discovery-questions-submit-early"));
      if (await submit.first().isVisible().catch(() => false)) {
        await submit.first().click();
        actions.push(`discovery@${round}`);
        await page.waitForTimeout(10000);
      }
    }

    if (await page.getByTestId("confirm-profile-btn").isVisible().catch(() => false)) {
      const btn = page.getByTestId("confirm-profile-btn");
      if (await btn.isEnabled().catch(() => false)) {
        await btn.click();
        actions.push(`confirm-profile@${round}`);
        await page.waitForTimeout(8000);
      }
    }

    if (await page.getByTestId("approve-evidence-btn").isVisible().catch(() => false)) {
      const btn = page.getByTestId("approve-evidence-btn");
      if (await btn.isEnabled().catch(() => false)) {
        await btn.click();
        actions.push(`approve-evidence@${round}`);
        await page.waitForTimeout(10000);
      }
    }

    if (await page.getByTestId("approve-all-eligible-assumptions-btn").isVisible().catch(() => false)) {
      const btn = page.getByTestId("approve-all-eligible-assumptions-btn");
      if (await btn.isEnabled().catch(() => false)) {
        await btn.click();
        actions.push(`approve-assumptions@${round}`);
        await page.waitForTimeout(12000);
      }
    }

    for (const id of ["continue-to-risks-btn", "continue-to-decision-btn"]) {
      const btn = page.getByTestId(id);
      if (await btn.isVisible().catch(() => false) && (await btn.isEnabled().catch(() => false))) {
        await btn.click();
        actions.push(`${id}@${round}`);
        await page.waitForTimeout(6000);
      }
    }

    // Nudge the agent when stuck mid-pipeline.
    if (round === 2 || round === 5 || round === 8 || round === 11) {
      const composer = page.locator("form input[type='text'], form textarea").first();
      if (await composer.isVisible().catch(() => false)) {
        await composer.fill(
          "Please continue the full study: market evidence with sources, research quality, assumptions, financial analysis, risks, and a clear invest/no-invest recommendation for a Saudi founder.",
        );
        await page.getByRole("button", { name: /Send|إرسال/ }).click();
        actions.push(`chat-nudge@${round}`);
        await page.waitForTimeout(15000);
      }
    }

    // Early exit if report ready.
    if (await page.getByTestId("in-study-report-panel").isVisible().catch(() => false)) {
      actions.push(`report-ready@${round}`);
      break;
    }
    if (await page.getByTestId("decision-panel").isVisible().catch(() => false)) {
      // Keep looping a bit to try continue-to-decision if risks not yet done.
      if (phasesSeen.has("REPORT_READY") || /REPORT/i.test(phaseText)) break;
    }

    await page.waitForTimeout(2000);
  }

  return { actions, phasesSeen: [...phasesSeen] };
}

async function snapshot(page: Page) {
  const phase = ((await page.getByTestId("study-phase").textContent().catch(() => "")) || "").trim();
  const mainText = (await page.getByTestId("v2-study-workspace").innerText().catch(() => "")) || "";

  // Try opening evidence drawer if RQ claims are present.
  const openDrawer = page.getByTestId("open-evidence-drawer").first();
  let drawerOpened = false;
  if (await openDrawer.isVisible().catch(() => false)) {
    await openDrawer.click();
    drawerOpened = await page.getByTestId("evidence-drawer").isVisible().catch(() => false);
  }

  return {
    url: page.url(),
    phase,
    hasResearchQuality: await page.getByTestId("research-quality-observability").isVisible().catch(() => false),
    hasResearchQualitySummary: await page.getByTestId("research-quality-summary").isVisible().catch(() => false),
    hasResearchQualityClaims: await page.getByTestId("research-quality-claims").isVisible().catch(() => false),
    drawerOpened,
    hasClaims: await page.getByTestId("claims-panel").isVisible().catch(() => false),
    hasAssumptions: await page
      .getByTestId("assumptions-panel")
      .or(page.getByTestId("assumption-review-panel"))
      .isVisible()
      .catch(() => false),
    hasDecision: await page.getByTestId("decision-panel").isVisible().catch(() => false),
    hasMarketResearch: await page.getByTestId("market-research-panel").isVisible().catch(() => false),
    hasIrr: await page.getByTestId("workspace-irr").isVisible().catch(() => false),
    hasFinancialPanel: await page.getByTestId("in-study-financial-panel").isVisible().catch(() => false),
    hasRisks: await page.getByTestId("in-study-risks-panel").isVisible().catch(() => false),
    hasReport: await page.getByTestId("in-study-report-panel").isVisible().catch(() => false),
    hasJourneyNav: await page.getByTestId("study-journey-nav").isVisible().catch(() => false),
    signals: {
      competitor: /competitor|منافس/i.test(mainText),
      pricing: /price|pricing|سعر|SAR|ريال/i.test(mainText),
      risk: /risk|مخاطر/i.test(mainText),
      evidence: /evidence|source|دليل|مصدر|official|رسمي|GASTAT|SAMA|ZATCA/i.test(mainText),
      assumption: /assumption|افتراض/i.test(mainText),
      freshness: /fresh|stale|current|حداثة|قديم|as.of|as_of/i.test(mainText),
      conflict: /conflict|تعارض/i.test(mainText),
      recommendation: /recommend|go|no.go|invest|verdict|قرار|توصية/i.test(mainText),
      supply: /supply|capex|recycl|مصنع|سلسلة|رأس المال/i.test(mainText),
      cac: /cac|ltv|acquisition|اشتراك|subscription|ZATCA/i.test(mainText),
    },
    excerpt: mainText.slice(0, 4000),
  };
}

function summarizeApi(body: any) {
  if (!body || typeof body !== "object") return null;
  const claims = Array.isArray(body.claims) ? body.claims : [];
  const assumptions = Array.isArray(body.assumptions) ? body.assumptions : [];
  const rq = body.research_quality_observability || body.research_context?.research_quality_observability;
  const claimSnips = claims.slice(0, 8).map((c: any) => ({
    statement: String(c.statement || c.text || c.claim || "").slice(0, 180),
    source: c.source_name || c.source || c.authority || c.provenance?.source || null,
    evidence_id: c.evidence_id || null,
    has_rq: Boolean(c.research_quality || c.provenance?.research_quality),
  }));
  const assumptionSnips = assumptions.slice(0, 12).map((a: any) => ({
    key: a.key || a.id,
    label: a.label_en || a.label || a.name,
    value: a.value,
    status: a.status || a.review_status,
    origin: a.origin,
  }));
  return {
    phase: body.phase,
    claims_count: body.claims_count ?? claims.length,
    assumptions_count: body.assumptions_count ?? assumptions.length,
    research_status: body.research_status,
    research_attempts: Array.isArray(body.research_attempts) ? body.research_attempts.length : 0,
    has_rq_observability: Boolean(rq),
    rq_summary: rq
      ? {
          overall_status: rq.overall_status || rq.status || rq.summary?.status,
          claim_count: rq.claims?.length || rq.claim_rows?.length || null,
          freshness: rq.freshness || rq.summary?.freshness || null,
          conflicts: rq.conflicts?.length || rq.summary?.conflicts || null,
        }
      : null,
    market_research_status: body.market_research_context?.status || null,
    verdict: body.verdict || null,
    decision_rationale: body.decision_rationale ? String(body.decision_rationale).slice(0, 500) : null,
    decision_risks: (body.decision_risks || []).slice(0, 8),
    financial_keys: body.financial_results ? Object.keys(body.financial_results).slice(0, 20) : [],
    claimSnips,
    assumptionSnips,
    knowledge_hit_count: body.knowledge_context?.hit_count ?? null,
    next_action: body.next_action || null,
    error: body.error || null,
  };
}

function score(
  snap: Awaited<ReturnType<typeof snapshot>>,
  actions: string[],
  api: ReturnType<typeof summarizeApi>,
) {
  const progressed = actions.length > 0 || Boolean(snap.phase);
  const structured =
    snap.hasClaims ||
    snap.hasAssumptions ||
    snap.hasDecision ||
    snap.hasMarketResearch ||
    Boolean(api && ((api.claims_count || 0) > 0 || (api.assumptions_count || 0) > 0));
  const ux = progressed ? (structured && snap.hasJourneyNav ? "PASS" : structured ? "PARTIAL" : "FAIL") : "FAIL";

  const research =
    snap.hasResearchQuality || api?.has_rq_observability
      ? "PASS"
      : snap.hasClaims || snap.signals.evidence || (api && (api.claims_count || 0) > 0)
        ? "PARTIAL"
        : "FAIL";

  const trust =
    snap.hasResearchQuality || (api?.has_rq_observability && snap.signals.evidence)
      ? "PASS"
      : snap.signals.evidence && (snap.hasClaims || (api && (api.claims_count || 0) > 0))
        ? "PARTIAL"
        : "FAIL";

  const value =
    snap.hasDecision || snap.hasReport || snap.hasIrr || Boolean(api?.verdict)
      ? "PASS"
      : snap.hasAssumptions || snap.hasRisks || snap.hasFinancialPanel || (api && (api.assumptions_count || 0) > 0)
        ? "PARTIAL"
        : "FAIL";

  return { ux, research_quality: research, trust, business_value: value };
}

test.describe.configure({ mode: "serial" });

for (const spec of CASES) {
  test(`Product validation ${spec.id}`, async ({ page }) => {
    ensureOut();
    const consoleErrors: string[] = [];
    page.on("console", (m) => {
      if (m.type() === "error" && !/favicon|React DevTools/i.test(m.text())) consoleErrors.push(m.text());
    });
    page.on("pageerror", (e) => consoleErrors.push(String(e)));

    const email = await registerUser(page, spec.id);
    await createProject(page, spec);
    const shots = [await shot(page, `${spec.id}-01-project.png`)];

    await openStudy(page, spec.briefing);
    shots.push(await shot(page, `${spec.id}-02-workspace-brief.png`) );

    const { actions, phasesSeen } = await progress(page, spec.archetypeId);
    shots.push(await shot(page, `${spec.id}-03-progress.png`));

    // Capture Arabic surface for bilingual product check.
    const toggle = page.getByLabel("Switch language");
    if (await toggle.count()) {
      await toggle.click();
      await page.waitForTimeout(800);
      shots.push(await shot(page, `${spec.id}-04-arabic.png`));
      await toggle.click();
      await page.waitForTimeout(500);
    }

    const snap = await snapshot(page);
    shots.push(await shot(page, `${spec.id}-05-final.png`));

    const apiRaw = await fetchStudyPayload(page);
    const api = summarizeApi(apiRaw?.body);
    fs.writeFileSync(path.join(OUT, `${spec.id}-study-api.json`), JSON.stringify(apiRaw, null, 2));

    const scores = score(snap, actions, api);

    const result = {
      id: spec.id,
      name: spec.name,
      email,
      actions,
      phasesSeen,
      snap,
      api,
      scores,
      screenshots: shots,
      consoleErrors: consoleErrors.slice(0, 25),
      notes: [
        !snap.hasResearchQuality && !api?.has_rq_observability
          ? "Research Quality Observability not present on natural research path for this run."
          : "Research Quality Observability present (UI and/or API).",
        !snap.hasDecision && !snap.hasIrr && !api?.verdict
          ? "No clear financial/decision verdict reached in this pass."
          : "Financial/decision output present.",
        phasesSeen.length ? `Phases observed: ${phasesSeen.join(" → ")}` : "No phase badge text captured.",
      ],
    };
    fs.writeFileSync(path.join(OUT, `${spec.id}-result.json`), JSON.stringify(result, null, 2));
    expect(page.url()).toMatch(/\/studies\//);
  });
}

test("write aggregate summary", async () => {
  ensureOut();
  const results = CASES.map((c) => {
    const p = path.join(OUT, `${c.id}-result.json`);
    return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : null;
  }).filter(Boolean);
  fs.writeFileSync(
    path.join(OUT, "aggregate-summary.json"),
    JSON.stringify(
      {
        generated_at: new Date().toISOString(),
        validation_code_sha: process.env.VALIDATION_CODE_SHA || "unknown",
        note: "Validated on Phase 8C.3 branch tip; main still at 8C.2 (PR #51 open at validation start).",
        results,
      },
      null,
      2,
    ),
  );
});
