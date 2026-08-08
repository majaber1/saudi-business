"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { listOpportunities, type Opportunity } from "@/lib/api";

const INDUSTRIES = ["technology", "healthcare", "retail", "industrial", "tourism", "education"] as const;
const RISK_LEVELS = ["low", "medium", "high"] as const;

const copy = {
  ar: {
    title: "الفرص الاستثمارية",
    subtitle: "أدخل المبلغ المتاح لديك لعرض الفرص التي تناسب ميزانيتك فقط، ثم صفِّ حسب القطاع ومستوى المخاطرة.",
    amountLabel: "المبلغ المتاح للاستثمار (ر.س)",
    amountPlaceholder: "مثال: 250000",
    industryLabel: "القطاع",
    riskLabel: "مستوى المخاطرة",
    all: "الكل",
    industryLabels: { technology: "تقنية", healthcare: "صحة", retail: "تجزئة", industrial: "صناعة", tourism: "سياحة", education: "تعليم" } as Record<string, string>,
    riskLabels: { low: "منخفضة", medium: "متوسطة", high: "مرتفعة" } as Record<string, string>,
    stageLabels: { idea: "فكرة", mvp: "نموذج أولي", early_revenue: "إيرادات مبكرة", growth: "نمو" } as Record<string, string>,
    ticket: "حجم التذكرة",
    expectedReturn: "العائد المتوقع (تقديري)",
    funded: "تم تمويله",
    unverified: "غير موثّق",
    empty: "لا توجد فرص مطابقة حاليًا لهذا المبلغ أو التصفية.",
    demoNote:
      "بيئة تجريبية: هذه القائمة تُقرأ من واجهة برمجية حقيقية وتتطلب تشغيلها وضبط قاعدة بيانات؛ عند عدم توفرها تظهر القائمة فارغة عوضًا عن بيانات وهمية.",
    disclaimer: "الأرقام أعلاه تقديرية وغير مضمونة وتتطلب دراسة جدوى مستقلة قبل أي قرار استثماري. لا تتم أي تحويلات مالية عبر هذه المنصة.",
    viewDetails: "التفاصيل",
  },
  en: {
    title: "Investment Opportunities",
    subtitle: "Enter what you have available to see only what fits your budget, then filter by industry and risk.",
    amountLabel: "Amount available to invest (SAR)",
    amountPlaceholder: "e.g. 250000",
    industryLabel: "Industry",
    riskLabel: "Risk level",
    all: "All",
    industryLabels: { technology: "Technology", healthcare: "Healthcare", retail: "Retail", industrial: "Industrial", tourism: "Tourism", education: "Education" } as Record<string, string>,
    riskLabels: { low: "Low", medium: "Medium", high: "High" } as Record<string, string>,
    stageLabels: { idea: "Idea", mvp: "MVP", early_revenue: "Early revenue", growth: "Growth" } as Record<string, string>,
    ticket: "Ticket size",
    expectedReturn: "Expected return (indicative)",
    funded: "funded",
    unverified: "unverified",
    empty: "No opportunities currently match this amount or filter.",
    demoNote:
      "Demo environment: this list is read from a real API and requires it running with a database configured; when unavailable the list shows empty rather than fabricated data.",
    disclaimer: "Figures above are indicative, not guaranteed, and require independent due diligence before any investment decision. No funds are transferred through this platform.",
    viewDetails: "Details",
  },
};

function fmtSAR(n: number | null, locale: "ar" | "en") {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n) + (locale === "ar" ? " ر.س" : " SAR");
}

export default function OpportunitiesPage() {
  const { locale } = useLanguage();
  const c = copy[locale];

  const [amount, setAmount] = useState<string>("");
  const [industry, setIndustry] = useState<string>("");
  const [risk, setRisk] = useState<string>("");
  const [items, setItems] = useState<Opportunity[] | null>(null);
  const [fetched, setFetched] = useState(false);

  useEffect(() => {
    const filters: { industry?: string; risk_level?: string; max_amount?: number } = {};
    if (industry) filters.industry = industry;
    if (risk) filters.risk_level = risk;
    const parsedAmount = parseFloat(amount);
    if (amount && !Number.isNaN(parsedAmount)) filters.max_amount = parsedAmount;

    let cancelled = false;
    listOpportunities(filters)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      })
      .finally(() => {
        if (!cancelled) setFetched(true);
      });
    return () => {
      cancelled = true;
    };
  }, [amount, industry, risk]);

  const riskBadgeClass: Record<string, string> = {
    low: "bg-emerald-50 text-emerald-700",
    medium: "bg-amber-50 text-amber-700",
    high: "bg-red-50 text-red-700",
  };

  return (
    <main className="container-page py-14">
      <h1 className="text-3xl font-bold tracking-tight text-ink-900">{c.title}</h1>
      <p className="mt-2 max-w-2xl text-ink-600">{c.subtitle}</p>

      {/* Filters */}
      <div className="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:grid-cols-3">
        <label className="block text-sm">
          <span className="text-ink-700">{c.amountLabel}</span>
          <input
            type="number"
            min={0}
            placeholder={c.amountPlaceholder}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
          />
        </label>
        <label className="block text-sm">
          <span className="text-ink-700">{c.industryLabel}</span>
          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-brand-500"
          >
            <option value="">{c.all}</option>
            {INDUSTRIES.map((i) => (
              <option key={i} value={i}>
                {c.industryLabels[i]}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="text-ink-700">{c.riskLabel}</span>
          <select
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 outline-none focus:border-brand-500"
          >
            <option value="">{c.all}</option>
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>
                {c.riskLabels[r]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Results */}
      {fetched && items && items.length === 0 && (
        <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center text-sm text-ink-600">
          {c.empty}
        </div>
      )}

      {items && items.length > 0 && (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((o) => {
            const progress =
              o.funding_goal && o.funding_goal > 0
                ? Math.min(100, Math.round(((o.funding_committed || 0) / o.funding_goal) * 100))
                : null;
            return (
              <div key={o.id} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-ink-900">{locale === "ar" ? o.title_ar : o.title_en}</h3>
                  <span className={"shrink-0 rounded-full px-2.5 py-1 text-xs font-medium " + (riskBadgeClass[o.risk_level] ?? riskBadgeClass.medium)}>
                    {c.riskLabels[o.risk_level] ?? o.risk_level}
                  </span>
                </div>
                <p className="mt-1 text-xs uppercase tracking-wide text-ink-500">
                  {c.industryLabels[o.industry] ?? o.industry} · {c.stageLabels[o.stage] ?? o.stage}
                </p>
                {(locale === "ar" ? o.summary_ar : o.summary_en) && (
                  <p className="mt-3 text-sm text-ink-600">{locale === "ar" ? o.summary_ar : o.summary_en}</p>
                )}
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-ink-500">{c.ticket}</p>
                    <p className="font-mono font-medium text-ink-900">
                      {fmtSAR(o.investment_min, locale)} – {fmtSAR(o.investment_max, locale)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-ink-500">{c.expectedReturn}</p>
                    <p className="font-mono font-medium text-ink-900">
                      {o.expected_return_percent !== null ? o.expected_return_percent + "%" : "—"}
                    </p>
                  </div>
                </div>
                {progress !== null && (
                  <div className="mt-4">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-gradient-to-r from-brand-500 to-gold-500" style={{ width: progress + "%" }} />
                    </div>
                    <p className="mt-1 text-xs text-ink-500">{progress}% {c.funded}</p>
                  </div>
                )}
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xs text-ink-500">
                    {o.verification_status === "demo" ? c.unverified : o.verification_status}
                  </span>
                  {o.source_url ? (
                    <Link href={o.source_url} className="text-sm font-medium text-brand-600 hover:underline">
                      {c.viewDetails}
                    </Link>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="mt-10 max-w-3xl text-xs text-ink-500">{c.disclaimer}</p>
      <p className="mt-2 max-w-3xl text-xs text-ink-500">{c.demoNote}</p>
    </main>
  );
}
