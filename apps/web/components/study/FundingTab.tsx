"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createAssumption,
  getBorrowingCapacity,
  getFinancialHealth,
  getFundingGap,
  listFinancialPeriods,
  saveFinancialPeriod,
  type BorrowingCapacity,
  type CompanyFinancialPeriod,
  type FinancialHealth,
  type FinancialPeriodUpdate,
  type FundingGap,
  type HealthMetric,
} from "@/lib/api";
import CollateralSection from "@/components/study/CollateralSection";

const copy = {
  ar: {
    intro: "تحليل التمويل مبني على البيانات المالية الفعلية للشركة المسجّلة أدناه. النتائج تقديرية للفحص الأولي وليست موافقة تمويلية.",
    disclaimer: "هذا تقدير أولي للفحص فقط، وليس موافقة من أي جهة تمويل. الموافقة النهائية تخضع لتحليل الائتمان الفعلي من الممول.",
    financialData: "البيانات المالية للشركة",
    addPeriod: "إضافة/تحديث فترة مالية",
    periodLabel: "الفترة (مثال FY2025)",
    save: "حفظ",
    saving: "جارٍ الحفظ...",
    savedPeriods: "الفترات المحفوظة",
    noPeriods: "لا توجد بيانات مالية محفوظة بعد. أضف فترة مالية لبدء تحليل التمويل.",
    health: "الصحة المالية",
    healthEmpty: "لا يمكن حساب الصحة المالية بعد. أضف بيانات الفترة المالية أعلاه.",
    fundingGap: "فجوة التمويل",
    requirement: "احتياج المشروع", ownerCapital: "رأس مال المالك", facilities: "التسهيلات المتاحة", gap: "فجوة التمويل",
    quickSetOwner: "تحديد رأس مال المالك (ر.س)",
    quickSetFacilities: "تحديد التسهيلات المتاحة (ر.س)",
    set: "تحديد",
    capacity: "القدرة التمويلية التقديرية",
    capacityEmpty: "لا يمكن تقدير القدرة التمويلية بعد.",
    missing: "بيانات ناقصة",
    baseCapacity: "القدرة الأساسية", stressCapacity: "القدرة في السيناريو الضاغط",
    primaryConstraint: "المحدد الرئيسي", secondaryConstraint: "المحدد الثانوي",
    financialSupport: "الدعم المالي",
    underwritingMissing: "متطلبات تحقق إضافية قبل التمويل الفعلي",
    statusLabels: { CALCULATED: "محسوبة", MISSING_DATA: "بيانات ناقصة", NOT_APPLICABLE: "غير قابل للتطبيق" } as Record<string, string>,
    sourceLabels: {
      financial_statement: "قوائم مالية", bank_statement: "كشف بنكي", user_confirmed: "مؤكد من المستخدم",
      audited_statement: "قوائم مدققة", management_account: "حسابات إدارية", unverified: "غير موثّق",
    } as Record<string, string>,
  },
  en: {
    intro: "Funding analysis is built from the actual company financial data recorded below. Results are an initial screening estimate, not a funding approval.",
    disclaimer: "This is an initial screening estimate only, not approval from any funder. Final approval is subject to the funder's actual credit assessment.",
    financialData: "Company financial data",
    addPeriod: "Add / update a financial period",
    periodLabel: "Period (e.g. FY2025)",
    save: "Save",
    saving: "Saving...",
    savedPeriods: "Saved periods",
    noPeriods: "No financial data saved yet. Add a financial period to start the funding analysis.",
    health: "Financial Health",
    healthEmpty: "Financial health cannot be calculated yet. Add financial period data above.",
    fundingGap: "Funding Gap",
    requirement: "Project requirement", ownerCapital: "Owner capital", facilities: "Available facilities", gap: "Funding gap",
    quickSetOwner: "Set owner contribution (SAR)",
    quickSetFacilities: "Set available facilities (SAR)",
    set: "Set",
    capacity: "Estimated Borrowing Capacity",
    capacityEmpty: "Borrowing capacity cannot be estimated yet.",
    missing: "Missing data",
    baseCapacity: "Base capacity", stressCapacity: "Stress-case capacity",
    primaryConstraint: "Primary constraint", secondaryConstraint: "Secondary constraint",
    financialSupport: "Financial support",
    underwritingMissing: "Additional validation required before real financing",
    statusLabels: { CALCULATED: "Calculated", MISSING_DATA: "Missing data", NOT_APPLICABLE: "Not applicable" } as Record<string, string>,
    sourceLabels: {
      financial_statement: "Financial statement", bank_statement: "Bank statement", user_confirmed: "User confirmed",
      audited_statement: "Audited statement", management_account: "Management account", unverified: "Unverified",
    } as Record<string, string>,
  },
};

const METRIC_ORDER = [
  "revenue_growth", "gross_margin", "ebitda_margin", "operating_margin", "net_margin",
  "working_capital", "current_ratio", "quick_ratio", "debt_to_equity", "debt_to_ebitda",
  "interest_coverage", "dscr",
];

const SUMMARY_ORDER = ["profitability", "liquidity", "leverage", "debt_service_capacity", "data_coverage"];

const SUMMARY_LABELS = {
  ar: { profitability: "الربحية", liquidity: "السيولة", leverage: "الرافعة المالية", debt_service_capacity: "قدرة خدمة الدين", data_coverage: "تغطية البيانات" },
  en: { profitability: "Profitability", liquidity: "Liquidity", leverage: "Leverage", debt_service_capacity: "Debt service capacity", data_coverage: "Data coverage" },
} as const;

const STATUS_STYLE: Record<string, string> = {
  CALCULATED: "bg-emerald-50 text-emerald-800",
  MISSING_DATA: "bg-amber-50 text-amber-800",
  NOT_APPLICABLE: "bg-slate-100 text-slate-600",
};

const SUMMARY_STYLE: Record<string, string> = {
  STRONG: "bg-emerald-50 text-emerald-800 border-emerald-200",
  ACCEPTABLE: "bg-sky-50 text-sky-800 border-sky-200",
  LOW: "bg-emerald-50 text-emerald-800 border-emerald-200",
  MODERATE: "bg-sky-50 text-sky-800 border-sky-200",
  WEAK: "bg-red-50 text-red-700 border-red-200",
  HIGH: "bg-red-50 text-red-700 border-red-200",
  FULL: "bg-emerald-50 text-emerald-800 border-emerald-200",
  PARTIAL: "bg-amber-50 text-amber-800 border-amber-200",
  MINIMAL: "bg-red-50 text-red-700 border-red-200",
  INSUFFICIENT_DATA: "bg-slate-100 text-slate-600 border-slate-200",
};

const FIELD_KEYS: (keyof FinancialPeriodUpdate)[] = [
  "revenue", "gross_profit", "ebitda", "operating_profit", "net_profit", "cash",
  "current_assets", "current_liabilities", "total_assets", "total_liabilities",
  "equity", "existing_debt", "annual_debt_service", "interest_expense",
  "accounts_receivable", "inventory", "capital_expenditure",
];

function fmt(n: number | null, locale: "ar" | "en") {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", { maximumFractionDigits: 0 }).format(n);
}

type Props = { token: string; studyId: number; locale: "ar" | "en" };

const emptyForm: Record<string, string> = Object.fromEntries(FIELD_KEYS.map((k) => [k, ""]));

export default function FundingTab({ token, studyId, locale }: Props) {
  const c = copy[locale];

  const [periods, setPeriods] = useState<CompanyFinancialPeriod[] | null>(null);
  const [health, setHealth] = useState<FinancialHealth | null | undefined>(undefined);
  const [gap, setGap] = useState<FundingGap | null>(null);
  const [capacity, setCapacity] = useState<BorrowingCapacity | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  const [periodLabel, setPeriodLabel] = useState("FY2025");
  const [source, setSource] = useState("user_confirmed");
  const [form, setForm] = useState<Record<string, string>>(emptyForm);
  const [busy, setBusy] = useState(false);

  const [ownerInput, setOwnerInput] = useState("");
  const [facilitiesInput, setFacilitiesInput] = useState("");
  const [assumptionBusy, setAssumptionBusy] = useState<"owner" | "facilities" | null>(null);

  const reload = useCallback(async () => {
    try {
      const [periodRows, healthRow, gapRow, capacityRow] = await Promise.all([
        listFinancialPeriods(token, studyId),
        getFinancialHealth(token, studyId),
        getFundingGap(token, studyId),
        getBorrowingCapacity(token, studyId),
      ]);
      setPeriods(periodRows);
      setHealth(healthRow);
      setGap(gapRow);
      setCapacity(capacityRow);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  }, [token, studyId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function onSavePeriod(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload: FinancialPeriodUpdate = { source: source as FinancialPeriodUpdate["source"] };
      for (const key of FIELD_KEYS) {
        const raw = form[key];
        if (raw !== "" && raw !== undefined) (payload as Record<string, number>)[key] = Number(raw);
      }
      await saveFinancialPeriod(token, studyId, periodLabel, payload);
      setForm(emptyForm);
      await reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function onSetAssumption(kind: "owner" | "facilities") {
    const value = kind === "owner" ? ownerInput : facilitiesInput;
    if (!value) return;
    setAssumptionBusy(kind);
    setError(null);
    try {
      const key = kind === "owner" ? "owner_contribution" : "existing_available_facilities";
      await createAssumption(token, studyId, {
        key,
        label_en: kind === "owner" ? "Owner contribution" : "Existing available facilities",
        label_ar: kind === "owner" ? "رأس مال المالك" : "التسهيلات المتاحة",
        value_number: Number(value),
        unit: "SAR",
        origin: "USER",
      });
      if (kind === "owner") setOwnerInput(""); else setFacilitiesInput("");
      const gapRow = await getFundingGap(token, studyId);
      setGap(gapRow);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setAssumptionBusy(null);
    }
  }

  return (
    <div className="mt-5 space-y-8">
      <p className="text-sm text-ink-600">{c.intro}</p>
      <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-900">{c.disclaimer}</p>
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {/* Company financial data */}
      <section>
        <h3 className="font-semibold text-ink-900">{c.financialData}</h3>
        {periods === null ? (
          <p className="mt-2 text-sm text-ink-500">…</p>
        ) : periods.length === 0 ? (
          <p className="mt-2 text-sm text-ink-500">{c.noPeriods}</p>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
            {periods.map((p) => (
              <span key={p.id} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-ink-700">
                {p.period} · {c.sourceLabels[p.source]} · {fmt(p.revenue, locale)} {locale === "ar" ? "ر.س إيراد" : "SAR revenue"}
              </span>
            ))}
          </div>
        )}

        <form onSubmit={onSavePeriod} className="mt-4 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-3">
          <h4 className="text-sm font-semibold text-ink-800 sm:col-span-3">{c.addPeriod}</h4>
          <label className="block text-sm">
            <span>{c.periodLabel}</span>
            <input value={periodLabel} onChange={(e) => setPeriodLabel(e.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" />
          </label>
          <label className="block text-sm sm:col-span-2">
            <span>{locale === "ar" ? "مصدر البيانات" : "Data source"}</span>
            <select value={source} onChange={(e) => setSource(e.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2">
              {Object.entries(c.sourceLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          {FIELD_KEYS.map((key) => (
            <label key={key} className="block text-sm">
              <span className="capitalize">{key.replace(/_/g, " ")}</span>
              <input
                type="number"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              />
            </label>
          ))}
          <div className="sm:col-span-3 flex justify-end">
            <button type="submit" disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60">
              {busy ? c.saving : c.save}
            </button>
          </div>
        </form>
      </section>

      {/* Financial health */}
      <section>
        <h3 className="font-semibold text-ink-900">{c.health}</h3>
        {health === undefined ? (
          <p className="mt-2 text-sm text-ink-500">…</p>
        ) : health === null ? (
          <p className="mt-2 text-sm text-ink-500">{c.healthEmpty}</p>
        ) : (
          <div className="mt-3">
            <div className="flex flex-wrap gap-2">
              {SUMMARY_ORDER.map((key) => (
                <span key={key} className={`rounded-full border px-3 py-1 text-xs font-semibold ${SUMMARY_STYLE[health.summary[key]] ?? ""}`}>
                  {SUMMARY_LABELS[locale][key as keyof (typeof SUMMARY_LABELS)["ar"]]}: {health.summary[key]}
                </span>
              ))}
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {METRIC_ORDER.filter((k) => health.metrics[k]).map((key) => {
                const m: HealthMetric = health.metrics[key];
                return (
                  <div key={key} className="flex items-center justify-between rounded-lg border border-slate-100 bg-white p-2 text-sm">
                    <span className="capitalize text-ink-600">{key.replace(/_/g, " ")}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[m.status]}`}>
                      {m.status === "CALCULATED" ? `${fmt(m.value, locale)}${m.unit === "percent" ? "%" : ""}` : c.statusLabels[m.status]}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* Funding gap */}
      <section>
        <h3 className="font-semibold text-ink-900">{c.fundingGap}</h3>
        {gap === null ? (
          <p className="mt-2 text-sm text-ink-500">…</p>
        ) : (
          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            <article className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-ink-500">{c.requirement}</p><p className="mt-1 font-semibold">{fmt(gap.total_project_requirement, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p></article>
            <article className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-ink-500">{c.ownerCapital}</p><p className="mt-1 font-semibold">{fmt(gap.owner_available_capital, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p>{gap.owner_available_capital_status === "MISSING_DATA" && <span className="text-xs text-amber-700">{c.statusLabels.MISSING_DATA}</span>}</article>
            <article className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-ink-500">{c.facilities}</p><p className="mt-1 font-semibold">{fmt(gap.existing_available_facilities, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p>{gap.existing_available_facilities_status === "MISSING_DATA" && <span className="text-xs text-amber-700">{c.statusLabels.MISSING_DATA}</span>}</article>
            <article className="rounded-xl bg-brand-50 p-3"><p className="text-xs text-brand-700">{c.gap}</p><p className="mt-1 font-semibold text-brand-900">{fmt(gap.funding_gap, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p></article>
          </div>
        )}
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="flex gap-2">
            <input type="number" placeholder={c.quickSetOwner} value={ownerInput} onChange={(e) => setOwnerInput(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
            <button onClick={() => onSetAssumption("owner")} disabled={assumptionBusy === "owner"} className="shrink-0 rounded-md border border-brand-500 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50 disabled:opacity-60">{c.set}</button>
          </div>
          <div className="flex gap-2">
            <input type="number" placeholder={c.quickSetFacilities} value={facilitiesInput} onChange={(e) => setFacilitiesInput(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
            <button onClick={() => onSetAssumption("facilities")} disabled={assumptionBusy === "facilities"} className="shrink-0 rounded-md border border-brand-500 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50 disabled:opacity-60">{c.set}</button>
          </div>
        </div>
      </section>

      {/* Borrowing capacity */}
      <section>
        <h3 className="font-semibold text-ink-900">{c.capacity}</h3>
        {capacity === undefined ? (
          <p className="mt-2 text-sm text-ink-500">…</p>
        ) : capacity === null || capacity.status === "INSUFFICIENT_DATA" ? (
          <div className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-ink-600">
            <p>{c.capacityEmpty}</p>
            {capacity?.missing_inputs && capacity.missing_inputs.length > 0 && (
              <p className="mt-1"><span className="font-medium">{c.missing}:</span> {capacity.missing_inputs.join(", ")}</p>
            )}
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <article className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">{c.baseCapacity}</p>
                <p className="mt-1 text-lg font-semibold text-emerald-900">{fmt(capacity.base_capacity, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p>
              </article>
              <article className="rounded-xl border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs text-amber-700">{c.stressCapacity}</p>
                <p className="mt-1 text-lg font-semibold text-amber-900">{fmt(capacity.stress_capacity, locale)} {locale === "ar" ? "ر.س" : "SAR"}</p>
              </article>
            </div>
            <p className="text-sm text-ink-700"><span className="font-medium">{c.primaryConstraint}:</span> {capacity.primary_constraint}</p>
            {capacity.secondary_constraint && <p className="text-sm text-ink-700"><span className="font-medium">{c.secondaryConstraint}:</span> {capacity.secondary_constraint}</p>}
            <p className="text-sm text-ink-700"><span className="font-medium">{c.financialSupport}:</span> <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${SUMMARY_STYLE[capacity.financial_support] ?? ""}`}>{capacity.financial_support}</span></p>
            {capacity.missing_inputs.length > 0 && <p className="text-sm text-amber-800"><span className="font-medium">{c.missing}:</span> {capacity.missing_inputs.join(", ")}</p>}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-ink-600">
              <p className="font-medium text-ink-800">{c.underwritingMissing}</p>
              <ul className="mt-1 list-inside list-disc">
                {capacity.missing_underwriting_inputs.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-900">{capacity.disclaimer}</p>
          </div>
        )}
      </section>

      <CollateralSection token={token} studyId={studyId} locale={locale} />
    </div>
  );
}
