"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { API_BASE } from "@/lib/api";

type Idea = {
  id: number;
  title_en: string;
  title_ar: string;
  industry: string;
  summary_en?: string | null;
  summary_ar?: string | null;
  revenue_model?: string | null;
  investment_min?: number | null;
  investment_max?: number | null;
  difficulty?: string | null;
  status: string;
};

const industries = [
  { value: "", ar: "جميع القطاعات", en: "All sectors" },
  { value: "Food & Beverage", ar: "الأغذية والمشروبات", en: "Food & Beverage" },
  { value: "Healthcare", ar: "الرعاية الصحية", en: "Healthcare" },
  { value: "Technology", ar: "التقنية", en: "Technology" },
  { value: "Education", ar: "التعليم", en: "Education" },
  { value: "Manufacturing", ar: "التصنيع", en: "Manufacturing" },
  { value: "Tourism", ar: "السياحة", en: "Tourism" },
  { value: "Retail", ar: "التجزئة", en: "Retail" },
  { value: "Logistics", ar: "الخدمات اللوجستية", en: "Logistics" },
];

function money(value: number, locale: "ar" | "en") {
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function IdeasPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const lang = locale as "ar" | "en";
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [industry, setIndustry] = useState("");

  useEffect(() => {
    setLoading(true);
    const qs = industry ? `?industry=${encodeURIComponent(industry)}` : "";
    fetch(`${API_BASE}/ideas/${qs}`)
      .then((r) => r.json())
      .then((data) => setIdeas(data))
      .catch(() => setIdeas([]))
      .finally(() => setLoading(false));
  }, [industry]);

  const difficultyVariant = (d?: string | null) =>
    d === "easy" ? "success" : d === "medium" ? "warning" : d === "hard" ? "danger" : "neutral";

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="💡"
        title={ar ? "بنك الأفكار" : "Idea Bank"}
        subtitle={ar
          ? "أفكار مشاريع متوافقة مع رؤية 2030 ومصنفة حسب القطاع"
          : "Vision 2030-aligned project ideas categorized by sector"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-center gap-4">
            <label className="text-sm font-medium text-ink-700">{ar ? "تصفية حسب القطاع" : "Filter by sector"}</label>
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-brand-500 focus:outline-none"
            >
              {industries.map((ind) => (
                <option key={ind.value} value={ind.value}>{ar ? ind.ar : ind.en}</option>
              ))}
            </select>
            <span className="text-sm text-ink-500">
              {ar ? `${ideas.length} فكرة` : `${ideas.length} ideas`}
            </span>
          </div>
        </section>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />
            ))}
          </div>
        ) : ideas.length === 0 ? (
          <EmptyState
            icon="💡"
            title={ar ? "لا توجد أفكار حاليًا" : "No ideas available"}
            description={ar
              ? "لم يتم نشر أفكار بعد في هذا القطاع. تحقق لاحقًا."
              : "No ideas have been published in this sector yet. Check back later."}
            actionLabel={ar ? "عرض جميع القطاعات" : "View all sectors"}
            onAction={() => setIndustry("")}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {ideas.map((idea) => (
              <article
                key={idea.id}
                className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card-hover"
              >
                <div className="flex items-start justify-between gap-2">
                  <Badge variant="brand">{idea.industry}</Badge>
                  {idea.difficulty && (
                    <Badge variant={difficultyVariant(idea.difficulty)}>{idea.difficulty}</Badge>
                  )}
                </div>
                <h3 className="mt-4 font-bold text-ink-900 group-hover:text-brand-700">
                  {ar ? idea.title_ar : idea.title_en}
                </h3>
                {(ar ? idea.summary_ar : idea.summary_en) && (
                  <p className="mt-2 line-clamp-3 text-sm leading-6 text-ink-600">
                    {ar ? idea.summary_ar : idea.summary_en}
                  </p>
                )}
                <div className="mt-4 flex flex-wrap gap-3 text-xs text-ink-500">
                  {idea.revenue_model && (
                    <span>{ar ? "نموذج الإيرادات" : "Revenue"}: {idea.revenue_model}</span>
                  )}
                  {idea.investment_min != null && idea.investment_max != null && (
                    <span>{money(idea.investment_min, lang)} – {money(idea.investment_max, lang)}</span>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}

        <section className="rounded-xl border border-green-200 bg-green-50 p-5">
          <h3 className="font-semibold text-green-800">{ar ? "رؤية 2030" : "Vision 2030"}</h3>
          <p className="mt-2 text-sm text-green-700">
            {ar
              ? "جميع الأفكار المعروضة متوافقة مع أهداف رؤية المملكة 2030 وتمثل فرصًا حقيقية في القطاعات المستهدفة."
              : "All ideas displayed are aligned with Saudi Vision 2030 goals and represent real opportunities in targeted sectors."}
          </p>
        </section>
      </div>
    </div>
  );
}
