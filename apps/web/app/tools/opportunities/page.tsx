"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { Badge } from "@/components/ui/Badge";
import { listOpportunities, type Opportunity } from "@/lib/api";

function money(value: number, locale: "ar" | "en") {
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency", currency: "SAR", maximumFractionDigits: 0,
  }).format(value);
}

const riskVariant = (level: string) => level === "low" ? "success" as const : level === "high" ? "danger" as const : "warning" as const;

export default function OpportunitiesServicePage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [industry, setIndustry] = useState("");
  const [risk, setRisk] = useState("");
  const [maxAmount, setMaxAmount] = useState("");

  useEffect(() => {
    setLoading(true);
    listOpportunities({
      industry: industry || undefined,
      risk_level: risk || undefined,
      max_amount: maxAmount ? Number(maxAmount) : undefined,
    })
      .then(setOpportunities)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [industry, risk, maxAmount]);

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="🎯"
        title={ar ? "الفرص الاستثمارية" : "Investment Opportunities"}
        subtitle={ar ? "تصفّح فرصًا مصنّفة حسب القطاع والمخاطر وحجم الاستثمار" : "Browse opportunities by sector, risk level, and investment size"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        <section className="flex flex-wrap gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none">
            <option value="">{ar ? "جميع القطاعات" : "All industries"}</option>
            <option value="technology">{ar ? "تقنية" : "Technology"}</option>
            <option value="food_beverage">{ar ? "أغذية ومشروبات" : "Food & Beverage"}</option>
            <option value="healthcare">{ar ? "رعاية صحية" : "Healthcare"}</option>
            <option value="manufacturing">{ar ? "تصنيع" : "Manufacturing"}</option>
            <option value="retail">{ar ? "تجزئة" : "Retail"}</option>
          </select>
          <select value={risk} onChange={(e) => setRisk(e.target.value)} className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none">
            <option value="">{ar ? "جميع المخاطر" : "All risk levels"}</option>
            <option value="low">{ar ? "منخفض" : "Low"}</option>
            <option value="medium">{ar ? "متوسط" : "Medium"}</option>
            <option value="high">{ar ? "مرتفع" : "High"}</option>
          </select>
          <input
            type="number"
            value={maxAmount}
            onChange={(e) => setMaxAmount(e.target.value)}
            placeholder={ar ? "الحد الأقصى للاستثمار" : "Max investment"}
            className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
          />
        </section>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}
          </div>
        ) : opportunities.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-6 py-16 text-center">
            <span className="mb-4 block text-5xl opacity-60">🔍</span>
            <p className="text-lg font-bold text-ink-700">{ar ? "لا توجد فرص مطابقة" : "No matching opportunities"}</p>
            <p className="mt-2 text-sm text-ink-500">{ar ? "جرّب تعديل الفلاتر." : "Try adjusting your filters."}</p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {opportunities.map((o) => (
              <article key={o.id} className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-bold text-ink-900">{ar ? o.title_ar : o.title_en}</h3>
                  <Badge variant={riskVariant(o.risk_level)}>
                    {o.risk_level === "low" ? (ar ? "منخفض" : "Low") : o.risk_level === "high" ? (ar ? "مرتفع" : "High") : (ar ? "متوسط" : "Medium")}
                  </Badge>
                </div>
                <p className="mt-2 text-sm text-ink-600 line-clamp-2">{ar ? o.summary_ar : o.summary_en}</p>
                <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-sm">
                  <div className="flex justify-between"><span className="text-ink-500">{ar ? "القطاع" : "Sector"}</span><span className="font-medium text-ink-700">{o.industry}</span></div>
                  {o.investment_min && <div className="flex justify-between"><span className="text-ink-500">{ar ? "الاستثمار" : "Investment"}</span><span className="font-medium text-ink-700">{money(o.investment_min, locale as "ar" | "en")}{o.investment_max ? ` — ${money(o.investment_max, locale as "ar" | "en")}` : ""}</span></div>}
                  {o.expected_return_percent && <div className="flex justify-between"><span className="text-ink-500">{ar ? "العائد المتوقع" : "Expected return"}</span><span className="font-medium text-brand-600">{o.expected_return_percent}%</span></div>}
                </div>
                {o.funding_goal && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-ink-500"><span>{ar ? "التقدم" : "Progress"}</span><span>{Math.round((o.funding_committed / o.funding_goal) * 100)}%</span></div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-brand-500" style={{ width: `${Math.min(100, (o.funding_committed / o.funding_goal) * 100)}%` }} />
                    </div>
                  </div>
                )}
                <div className="mt-3 flex items-center gap-2">
                  <Badge variant={o.verification_status === "verified" ? "success" : o.verification_status === "demo" ? "neutral" : "warning"}>
                    {o.verification_status === "verified" ? (ar ? "موثّق" : "Verified") : o.verification_status === "demo" ? (ar ? "عرض توضيحي" : "Demo") : (ar ? "قيد المراجعة" : "Under review")}
                  </Badge>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
