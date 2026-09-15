"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import {
  getToken,
  listProjects,
  listStudies,
  getSimulatorVariables,
  runSimulation,
  listScenarios,
  type Project,
  type Study,
  type SimulatorVariable,
  type SimulatorVariablesMeta,
  type SimulationResult,
  type ScenarioRunOut,
} from "@/lib/api";
import { archetypeLabel } from "@/lib/archetypeLabels";

type Phase = "select" | "configure" | "result" | "compare";

const VERDICT_COLORS: Record<string, string> = {
  feasible: "bg-emerald-100 text-emerald-800",
  borderline: "bg-amber-100 text-amber-800",
  not_feasible: "bg-red-100 text-red-800",
};

const DECISION_COLORS: Record<string, string> = {
  GO: "bg-emerald-100 text-emerald-800",
  CONDITIONAL_GO: "bg-amber-100 text-amber-800",
  NO_GO: "bg-red-100 text-red-800",
  INSUFFICIENT_EVIDENCE: "bg-slate-100 text-slate-800",
};

function fmtSAR(v: number | null | undefined, locale: string): string {
  if (v == null) return "—";
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(v);
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}

function DeltaCell({ d, locale, isCurrency }: { d: { baseline: any; scenario: any; absolute: any; percent?: any } | undefined; locale: string; isCurrency?: boolean }) {
  if (!d) return <td className="px-3 py-2 text-sm text-ink-500">—</td>;
  const abs = d.absolute;
  const color = abs == null ? "text-ink-500" : abs > 0 ? "text-emerald-700" : abs < 0 ? "text-red-700" : "text-ink-500";
  return (
    <td className={`px-3 py-2 text-sm ${color}`}>
      {isCurrency ? fmtSAR(abs, locale) : fmtNum(abs)}
      {d.percent != null && <span className="ms-1 text-xs">({fmtPct(d.percent)})</span>}
    </td>
  );
}

export default function SimulatorPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const token = getToken();

  const [phase, setPhase] = useState<Phase>("select");
  const [projects, setProjects] = useState<Project[]>([]);
  const [studies, setStudies] = useState<Study[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedStudy, setSelectedStudy] = useState<Study | null>(null);
  const [variablesMeta, setVariablesMeta] = useState<SimulatorVariablesMeta | null>(null);
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [scenarioName, setScenarioName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<ScenarioRunOut[]>([]);
  const [compareIds, setCompareIds] = useState<number[]>([]);

  useEffect(() => {
    if (!token) return;
    listProjects(token)
      .then(setProjects)
      .catch((e) => setError(e.message));
  }, [token]);

  const handleSelectProject = useCallback(
    async (p: Project) => {
      if (!token) return;
      setSelectedProject(p);
      setError("");
      try {
        const ss = await listStudies(token, p.id);
        setStudies(ss);
        if (ss.length === 1) {
          handleSelectStudy(ss[0]);
        }
      } catch (e: any) {
        setError(e.message);
      }
    },
    [token],
  );

  const handleSelectStudy = useCallback(
    async (s: Study) => {
      if (!token) return;
      setSelectedStudy(s);
      setError("");
      setLoading(true);
      try {
        const [meta, scenarios] = await Promise.all([
          getSimulatorVariables(token, s.id),
          listScenarios(token, s.id),
        ]);
        setVariablesMeta(meta);
        setSavedScenarios(scenarios);
        setOverrides({});
        setScenarioName("");
        setResult(null);
        setPhase("configure");
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [token],
  );

  const handleRunSimulation = useCallback(async () => {
    if (!token || !selectedStudy) return;
    const activeOverrides: Record<string, number> = {};
    for (const [key, val] of Object.entries(overrides)) {
      if (variablesMeta && variablesMeta.current_values[key] !== val) {
        activeOverrides[key] = val;
      }
    }
    if (Object.keys(activeOverrides).length === 0) {
      setError(ar ? "غيّر قيمة واحدة على الأقل لتشغيل المحاكاة." : "Change at least one value to run the simulation.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await runSimulation(token, selectedStudy.id, {
        scenario_name: scenarioName || (ar ? "سيناريو مخصص" : "Custom Scenario"),
        assumption_overrides: activeOverrides,
      });
      setResult(res);
      setSavedScenarios((prev) => [res.scenario as any, ...prev]);
      setPhase("result");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token, selectedStudy, overrides, variablesMeta, scenarioName, ar]);

  const handleCompare = useCallback(() => {
    setPhase("compare");
  }, []);

  const handleNewScenario = useCallback(() => {
    setOverrides({});
    setScenarioName("");
    setResult(null);
    setPhase("configure");
  }, []);

  const handleBack = useCallback(() => {
    if (phase === "result" || phase === "compare") {
      setPhase("configure");
    } else if (phase === "configure") {
      setPhase("select");
      setSelectedProject(null);
      setSelectedStudy(null);
      setVariablesMeta(null);
    }
  }, [phase]);

  const comparedScenarios = useMemo(() => {
    if (compareIds.length === 0) return savedScenarios.slice(0, 3);
    return savedScenarios.filter((s) => compareIds.includes(s.id));
  }, [savedScenarios, compareIds]);

  if (!token) {
    return (
      <main className="container-page py-16 text-center">
        <p className="text-ink-600">{ar ? "سجّل الدخول لاستخدام محاكي القرارات." : "Sign in to use the Decision Simulator."}</p>
        <Link href="/login?next=/tools/simulator" className="mt-4 inline-flex rounded-lg bg-brand-600 px-5 py-2.5 text-white hover:bg-brand-700">
          {ar ? "تسجيل الدخول" : "Sign In"}
        </Link>
      </main>
    );
  }

  return (
    <>
      <ServiceHeader
        icon="▦"
        title={ar ? "محاكي القرارات" : "Decision Simulator"}
        subtitle={ar ? "اختبر سيناريوهات افتراضية قبل اتخاذ القرار الحقيقي" : "Test what-if scenarios before making the real decision"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
        actions={
          phase !== "select" ? (
            <button onClick={handleBack} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50" data-testid="simulator-back">
              {ar ? "رجوع" : "Back"}
            </button>
          ) : undefined
        }
      />

      <main className="container-page py-8" data-testid="simulator-page">
        {error && (
          <div className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-700" role="alert" data-testid="simulator-error">
            {error}
          </div>
        )}

        {/* PHASE: Select Business & Study */}
        {phase === "select" && (
          <div data-testid="simulator-select">
            <h2 className="mb-4 text-lg font-bold text-ink-900">{ar ? "اختر العمل والدراسة الأساسية" : "Select Business & Baseline Study"}</h2>
            {projects.length === 0 && !loading ? (
              <p className="text-sm text-ink-500">{ar ? "لا توجد أعمال. أنشئ عملاً جديداً أولاً." : "No businesses found. Create a new business first."}</p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {projects.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelectProject(p)}
                    className={`rounded-xl border p-4 text-start transition hover:border-brand-400 hover:shadow-md ${selectedProject?.id === p.id ? "border-brand-500 bg-brand-50" : "border-slate-200 bg-white"}`}
                    data-testid={`simulator-project-${p.id}`}
                  >
                    <p className="font-semibold text-ink-900">{p.name}</p>
                    <p className="mt-1 text-xs text-ink-500">{p.industry} · {fmtSAR(p.investment, locale)}</p>
                  </button>
                ))}
              </div>
            )}

            {selectedProject && studies.length > 1 && (
              <div className="mt-6">
                <h3 className="mb-3 font-semibold text-ink-800">{ar ? "اختر الدراسة" : "Select Study"}</h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {studies.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => handleSelectStudy(s)}
                      className="rounded-xl border border-slate-200 bg-white p-4 text-start transition hover:border-brand-400"
                      data-testid={`simulator-study-${s.id}`}
                    >
                      <p className="font-medium text-ink-900">{ar ? `دراسة #${s.id}` : `Study #${s.id}`}</p>
                      <p className="mt-1 text-xs text-ink-500">{s.status} · {s.current_step}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* PHASE: Configure Scenario */}
        {phase === "configure" && variablesMeta && selectedStudy && selectedProject && (
          <div data-testid="simulator-configure">
            {/* Header info */}
            <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <p className="text-xs text-ink-500">{ar ? "العمل" : "Business"}</p>
                  <p className="font-semibold text-ink-900">{selectedProject.name}</p>
                </div>
                <div>
                  <p className="text-xs text-ink-500">{ar ? "الدراسة" : "Study"}</p>
                  <p className="font-semibold text-ink-900">#{selectedStudy.id}</p>
                </div>
                {variablesMeta.archetype && (
                  <div>
                    <p className="text-xs text-ink-500">{ar ? "النوع" : "Archetype"}</p>
                    <p className="font-semibold text-ink-900">{archetypeLabel(variablesMeta.archetype, locale)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Scenario name */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-ink-700">
                {ar ? "اسم السيناريو" : "Scenario Name"}
                <input
                  type="text"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  placeholder={ar ? "سيناريو مخصص" : "Custom Scenario"}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
                  data-testid="scenario-name-input"
                />
              </label>
            </div>

            {/* Variable controls */}
            <div className="mb-6 rounded-xl border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-5 py-3">
                <h3 className="font-bold text-ink-900">{ar ? "المتغيرات" : "Variables"}</h3>
                <p className="mt-0.5 text-xs text-ink-500">{ar ? "عدّل القيم لاختبار سيناريو افتراضي" : "Adjust values to test a hypothetical scenario"}</p>
              </div>
              <div className="divide-y divide-slate-100">
                {variablesMeta.variables.map((v) => {
                  const current = variablesMeta.current_values[v.key] ?? 0;
                  const override = overrides[v.key] ?? current;
                  const changed = override !== current;
                  const isPercent = v.unit === "%";
                  return (
                    <div key={v.key} className="flex flex-col gap-2 px-5 py-3 sm:flex-row sm:items-center sm:gap-4">
                      <div className="min-w-[200px]">
                        <p className="text-sm font-medium text-ink-800">{ar ? v.ar : v.en}</p>
                        <p className="text-xs text-ink-500">
                          {ar ? "الحالي:" : "Current:"}{" "}
                          {isPercent ? `${(current * 100).toFixed(1)}%` : fmtSAR(current, locale)}
                        </p>
                      </div>
                      <div className="flex flex-1 items-center gap-3">
                        <input
                          type="number"
                          value={isPercent ? (override * 100).toFixed(1) : override}
                          onChange={(e) => {
                            const raw = parseFloat(e.target.value) || 0;
                            setOverrides((prev) => ({ ...prev, [v.key]: isPercent ? raw / 100 : raw }));
                          }}
                          step={isPercent ? 0.5 : v.key === "horizon_years" ? 1 : 1000}
                          className={`w-32 rounded-lg border px-3 py-1.5 text-sm ${changed ? "border-brand-500 bg-brand-50" : "border-slate-300"}`}
                          data-testid={`simulator-input-${v.key}`}
                        />
                        <span className="text-xs text-ink-500">{v.unit === "SAR" ? "SAR" : v.unit}</span>
                        {changed && (
                          <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-700">
                            {ar ? "افتراض سيناريو" : "SCENARIO"}
                          </span>
                        )}
                      </div>
                      {changed && (
                        <button
                          onClick={() => setOverrides((prev) => { const n = { ...prev }; delete n[v.key]; return n; })}
                          className="text-xs text-ink-400 hover:text-red-600"
                        >
                          {ar ? "إعادة" : "Reset"}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Run button */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleRunSimulation}
                disabled={loading}
                className="rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
                data-testid="run-simulation-btn"
              >
                {loading ? (ar ? "جارٍ الحساب..." : "Computing...") : ar ? "تشغيل المحاكاة" : "Run Simulation"}
              </button>
              {savedScenarios.length > 0 && (
                <button
                  onClick={handleCompare}
                  className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-ink-700 hover:bg-slate-50"
                  data-testid="compare-scenarios-btn"
                >
                  {ar ? `مقارنة (${savedScenarios.length})` : `Compare (${savedScenarios.length})`}
                </button>
              )}
            </div>

            {/* Saved scenarios */}
            {savedScenarios.length > 0 && (
              <div className="mt-8">
                <h3 className="mb-3 font-bold text-ink-900">{ar ? "السيناريوهات المحفوظة" : "Saved Scenarios"}</h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {savedScenarios.map((s) => (
                    <div key={s.id} className="rounded-xl border border-slate-200 bg-white p-4" data-testid={`saved-scenario-${s.id}`}>
                      <p className="font-medium text-ink-900">{s.scenario_name}</p>
                      <p className="mt-1 text-xs text-ink-500">{s.scenario_type}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {Object.entries(s.assumption_overrides).map(([key, val]) => (
                          <span key={key} className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-700">
                            {key}: {typeof val === "number" ? val.toLocaleString() : val}
                          </span>
                        ))}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs">
                        <span className={`rounded px-1.5 py-0.5 font-bold ${VERDICT_COLORS[s.financial_result_snapshot?.verdict] || "bg-slate-100 text-slate-700"}`}>
                          {s.financial_result_snapshot?.verdict || "—"}
                        </span>
                        <span className="text-ink-500">NPV: {fmtSAR(s.financial_result_snapshot?.npv, locale)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* PHASE: Result */}
        {phase === "result" && result && (
          <div data-testid="simulator-result">
            {/* Hypothetical banner */}
            <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" data-testid="hypothetical-banner">
              {ar
                ? "⚠ سيناريو افتراضي — هذه ليست نتيجة اعتماد مالي حقيقي. لا تتأثر الدراسة الأصلية."
                : "⚠ HYPOTHETICAL SCENARIO — This is not an approved financial outcome. The original study is unchanged."}
            </div>

            {/* Financial comparison table */}
            <div className="mb-6 overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="w-full text-sm" data-testid="result-comparison-table">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-3 py-2 text-start font-semibold text-ink-700">{ar ? "المقياس" : "Metric"}</th>
                    <th className="px-3 py-2 text-start font-semibold text-ink-700">{ar ? "الأساس" : "Baseline"}</th>
                    <th className="px-3 py-2 text-start font-semibold text-ink-700">{ar ? "السيناريو" : "Scenario"}</th>
                    <th className="px-3 py-2 text-start font-semibold text-ink-700">{ar ? "الفرق" : "Delta"}</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: "annual_revenue", label: ar ? "الإيراد السنوي" : "Annual Revenue", currency: true },
                    { key: "annual_opex", label: ar ? "تكاليف التشغيل" : "Operating Costs", currency: true },
                    { key: "operating_result", label: ar ? "النتيجة التشغيلية" : "Operating Result", currency: true },
                    { key: "investment", label: ar ? "الاستثمار" : "Investment (CAPEX)", currency: true },
                    { key: "npv", label: "NPV", currency: true },
                    { key: "roi_percent", label: "ROI %", currency: false },
                    { key: "irr", label: "IRR", currency: false },
                    { key: "payback_years", label: ar ? "فترة الاسترداد" : "Payback (years)", currency: false },
                  ].map(({ key, label, currency }) => {
                    const d = result.delta[key];
                    return (
                      <tr key={key} className="border-b border-slate-50">
                        <td className="px-3 py-2 font-medium text-ink-800">{label}</td>
                        <td className="px-3 py-2 text-sm text-ink-600">
                          {currency ? fmtSAR(d?.baseline, locale) : fmtNum(d?.baseline)}
                        </td>
                        <td className="px-3 py-2 text-sm text-ink-600">
                          {currency ? fmtSAR(d?.scenario, locale) : fmtNum(d?.scenario)}
                        </td>
                        <DeltaCell d={d} locale={locale} isCurrency={currency} />
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Verdict comparison */}
            <div className="mb-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <p className="text-xs font-bold uppercase text-ink-500">{ar ? "الحكم الأساسي" : "Baseline Verdict"}</p>
                <span className={`mt-2 inline-block rounded px-2 py-1 text-sm font-bold ${VERDICT_COLORS[result.baseline?.verdict] || "bg-slate-100"}`}>
                  {result.baseline?.verdict || "—"}
                </span>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <p className="text-xs font-bold uppercase text-ink-500">{ar ? "حكم السيناريو" : "Scenario Verdict"}</p>
                <span className={`mt-2 inline-block rounded px-2 py-1 text-sm font-bold ${VERDICT_COLORS[result.scenario.financial_result_snapshot?.verdict] || "bg-slate-100"}`}>
                  {result.scenario.financial_result_snapshot?.verdict || "—"}
                </span>
              </div>
            </div>

            {/* Decision impact */}
            <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5" data-testid="decision-impact">
              <h3 className="mb-3 font-bold text-ink-900">{ar ? "أثر القرار" : "Decision Impact"}</h3>
              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <p className="text-xs text-ink-500">{ar ? "القرار الأساسي" : "Baseline Decision"}</p>
                  <span className={`mt-1 inline-block rounded px-2 py-1 text-sm font-bold ${DECISION_COLORS[result.decision_impact.baseline_decision] || "bg-slate-100"}`}>
                    {result.decision_impact.baseline_decision}
                  </span>
                </div>
                <span className="text-ink-400">→</span>
                <div>
                  <p className="text-xs text-ink-500">{ar ? "قرار السيناريو" : "Scenario Decision"}</p>
                  <span className={`mt-1 inline-block rounded px-2 py-1 text-sm font-bold ${DECISION_COLORS[result.decision_impact.scenario_decision] || "bg-slate-100"}`}>
                    {result.decision_impact.scenario_decision}
                  </span>
                </div>
              </div>
              <p className="mt-3 text-sm text-ink-600">{result.decision_impact.scenario_reason}</p>
              {result.decision_impact.changed && (
                <div className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                  {ar ? "⚠ تغيّر القرار بناءً على هذا السيناريو الافتراضي." : "⚠ Decision changed under this hypothetical scenario."}
                </div>
              )}
            </div>

            {/* Risk impact */}
            {result.risk_impact.length > 0 && (
              <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5" data-testid="risk-impact">
                <h3 className="mb-3 font-bold text-ink-900">{ar ? "أثر المخاطر" : "Risk Impact"}</h3>
                <div className="space-y-2">
                  {result.risk_impact.map((r, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm">
                      <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${
                        r.direction === "improved" ? "bg-emerald-100 text-emerald-700" : r.direction === "worsened" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"
                      }`}>
                        {r.direction === "improved" ? (ar ? "تحسّن" : "Improved") : r.direction === "worsened" ? (ar ? "تدهور" : "Worsened") : ar ? "افتراض سيناريو" : "Scenario"}
                      </span>
                      <span className="text-ink-700">{r.category.replace(/_/g, " ")}</span>
                      {r.change_pct != null && <span className="text-xs text-ink-500">{fmtPct(r.change_pct)}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence trust */}
            <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5" data-testid="trust-panel">
              <h3 className="mb-3 font-bold text-ink-900">{ar ? "جودة الأدلة والثقة" : "Evidence & Trust"}</h3>
              <div className="flex flex-wrap gap-3">
                <span className={`rounded px-2 py-1 text-sm font-bold ${
                  result.trust.grade === "INVESTMENT_GRADE" ? "bg-emerald-100 text-emerald-800" : result.trust.grade === "MODERATE_TRUST" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                }`}>
                  {result.trust.grade}
                </span>
                <span className="text-sm text-ink-500">{result.trust.verified_pct}% {ar ? "تحقق" : "verified"}</span>
              </div>
              <p className="mt-2 text-xs text-ink-500">{result.trust.note}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(result.trust.counts).map(([cls, count]) => (
                  <span key={cls} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-ink-600">
                    {cls}: {count}
                  </span>
                ))}
              </div>
            </div>

            {/* Sensitivity */}
            {result.scenario.financial_result_snapshot?.sensitivity && (
              <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5" data-testid="sensitivity-panel">
                <h3 className="mb-3 font-bold text-ink-900">{ar ? "تحليل الحساسية" : "Sensitivity Analysis"}</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="px-3 py-2 text-start text-ink-500">{ar ? "تغيير الإيراد" : "Revenue Change"}</th>
                        <th className="px-3 py-2 text-start text-ink-500">NPV</th>
                        <th className="px-3 py-2 text-start text-ink-500">IRR %</th>
                        <th className="px-3 py-2 text-start text-ink-500">{ar ? "الحكم" : "Verdict"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(result.scenario.financial_result_snapshot.sensitivity as any[]).map((row, i) => (
                        <tr key={i} className="border-b border-slate-50">
                          <td className="px-3 py-2">{row.revenue_change_percent > 0 ? "+" : ""}{row.revenue_change_percent}%</td>
                          <td className="px-3 py-2">{fmtSAR(row.npv, locale)}</td>
                          <td className="px-3 py-2">{row.irr_percent != null ? `${row.irr_percent.toFixed(1)}%` : "—"}</td>
                          <td className="px-3 py-2">
                            <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${VERDICT_COLORS[row.verdict] || "bg-slate-100"}`}>
                              {row.verdict}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <ul className="list-disc ps-4 text-sm text-amber-800">
                  {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <button onClick={handleNewScenario} className="rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700" data-testid="new-scenario-btn">
                {ar ? "سيناريو جديد" : "New Scenario"}
              </button>
              {savedScenarios.length > 1 && (
                <button onClick={handleCompare} className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-ink-700 hover:bg-slate-50" data-testid="compare-btn">
                  {ar ? "مقارنة السيناريوهات" : "Compare Scenarios"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* PHASE: Compare */}
        {phase === "compare" && (
          <div data-testid="simulator-compare">
            <h2 className="mb-4 text-lg font-bold text-ink-900">{ar ? "مقارنة السيناريوهات" : "Compare Scenarios"}</h2>
            {comparedScenarios.length === 0 ? (
              <p className="text-sm text-ink-500">{ar ? "لا توجد سيناريوهات للمقارنة." : "No scenarios to compare."}</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
                <table className="w-full text-sm" data-testid="compare-table">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50">
                      <th className="px-3 py-2 text-start font-semibold text-ink-700">{ar ? "المقياس" : "Metric"}</th>
                      {comparedScenarios.map((s) => (
                        <th key={s.id} className="px-3 py-2 text-start font-semibold text-ink-700">{s.scenario_name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { key: "investment", label: ar ? "الاستثمار" : "Investment", currency: true },
                      { key: "npv", label: "NPV", currency: true },
                      { key: "irr", label: "IRR", currency: false },
                      { key: "roi_percent", label: "ROI %", currency: false },
                      { key: "payback_years", label: ar ? "الاسترداد" : "Payback", currency: false },
                      { key: "verdict", label: ar ? "الحكم" : "Verdict", currency: false },
                    ].map(({ key, label, currency }) => (
                      <tr key={key} className="border-b border-slate-50">
                        <td className="px-3 py-2 font-medium text-ink-800">{label}</td>
                        {comparedScenarios.map((s) => {
                          const snap = s.financial_result_snapshot;
                          const val = snap?.[key];
                          return (
                            <td key={s.id} className="px-3 py-2 text-ink-600">
                              {key === "verdict" ? (
                                <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${VERDICT_COLORS[val] || "bg-slate-100"}`}>{val || "—"}</span>
                              ) : currency ? (
                                fmtSAR(val, locale)
                              ) : key === "irr" ? (
                                val != null ? `${(val * 100).toFixed(1)}%` : "—"
                              ) : (
                                fmtNum(val)
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-4">
              <button onClick={handleNewScenario} className="rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700">
                {ar ? "سيناريو جديد" : "New Scenario"}
              </button>
            </div>
          </div>
        )}

        {loading && phase === "select" && (
          <div className="mt-8 text-center text-ink-500">{ar ? "جارٍ التحميل..." : "Loading..."}</div>
        )}
      </main>
    </>
  );
}
