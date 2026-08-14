"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { Badge } from "@/components/ui/Badge";
import { matchFunding, type FundingMatch } from "@/lib/api";

const industries = [
  { value: "technology", ar: "تقنية", en: "Technology" },
  { value: "food_beverage", ar: "أغذية ومشروبات", en: "Food & Beverage" },
  { value: "healthcare", ar: "رعاية صحية", en: "Healthcare" },
  { value: "manufacturing", ar: "تصنيع", en: "Manufacturing" },
  { value: "retail", ar: "تجزئة", en: "Retail" },
  { value: "logistics", ar: "خدمات لوجستية", en: "Logistics" },
  { value: "education", ar: "تعليم", en: "Education" },
  { value: "energy", ar: "طاقة", en: "Energy" },
  { value: "real_estate", ar: "عقارات", en: "Real Estate" },
  { value: "other", ar: "أخرى", en: "Other" },
];

const stages = [
  { value: "idea", ar: "فكرة", en: "Idea" },
  { value: "mvp", ar: "منتج أولي", en: "MVP" },
  { value: "early_revenue", ar: "إيرادات أولية", en: "Early Revenue" },
  { value: "growth", ar: "نمو", en: "Growth" },
];

export default function FundingMatcherPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [industry, setIndustry] = useState("");
  const [stage, setStage] = useState("");
  const [hasMvp, setHasMvp] = useState(false);
  const [hasTeam, setHasTeam] = useState(false);
  const [results, setResults] = useState<FundingMatch[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!industry) { setError(ar ? "اختر القطاع" : "Select an industry"); return; }
    setError("");
    setLoading(true);
    try {
      const r = await matchFunding({ industry, stage: stage || undefined, has_mvp: hasMvp, has_technical_team: hasTeam });
      setResults(r);
    } catch {
      setError(ar ? "حدث خطأ" : "An error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="🏦"
        title={ar ? "مطابقة التمويل" : "Funding Matcher"}
        subtitle={ar ? "مطابقة شفّافة مع برامج التمويل السعودية الرسمية" : "Transparent matching with official Saudi funding programs"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        <div className="grid gap-8 lg:grid-cols-[400px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
            <h2 className="text-lg font-bold text-ink-900">{ar ? "بيانات المطابقة" : "Matching criteria"}</h2>

            <form onSubmit={handleSubmit} className="mt-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-ink-700">{ar ? "القطاع" : "Industry"}</label>
                <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-brand-500 focus:outline-none">
                  <option value="">{ar ? "اختر القطاع" : "Select industry"}</option>
                  {industries.map((i) => <option key={i.value} value={i.value}>{ar ? i.ar : i.en}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-ink-700">{ar ? "المرحلة" : "Stage"}</label>
                <select value={stage} onChange={(e) => setStage(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-brand-500 focus:outline-none">
                  <option value="">{ar ? "اختياري" : "Optional"}</option>
                  {stages.map((s) => <option key={s.value} value={s.value}>{ar ? s.ar : s.en}</option>)}
                </select>
              </div>
              <label className="flex items-center gap-3">
                <input type="checkbox" checked={hasMvp} onChange={(e) => setHasMvp(e.target.checked)} className="h-4 w-4 rounded border-slate-300 text-brand-600" />
                <span className="text-sm text-ink-700">{ar ? "لدي منتج أولي (MVP)" : "I have an MVP"}</span>
              </label>
              <label className="flex items-center gap-3">
                <input type="checkbox" checked={hasTeam} onChange={(e) => setHasTeam(e.target.checked)} className="h-4 w-4 rounded border-slate-300 text-brand-600" />
                <span className="text-sm text-ink-700">{ar ? "لدي فريق تقني" : "I have a technical team"}</span>
              </label>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <button type="submit" disabled={loading} className="w-full rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-card hover:bg-brand-700 disabled:opacity-50">
                {loading ? (ar ? "جارٍ البحث..." : "Searching...") : (ar ? "ابحث عن تمويل" : "Find funding")}
              </button>
            </form>

            <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4">
              <p className="text-xs text-blue-700">
                {ar
                  ? "💡 يمكنك استخدام بيانات مشروعك الحالي لتعبئة الحقول تلقائيًا."
                  : "💡 You can use your existing business profile to auto-fill these fields."}
              </p>
            </div>
          </section>

          <section>
            {results === null ? (
              <div className="flex h-full items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-16 text-center">
                <div>
                  <span className="mb-4 block text-5xl opacity-40">🏦</span>
                  <p className="text-sm text-ink-500">{ar ? "أدخل بياناتك لعرض البرامج المتاحة" : "Enter your criteria to see available programs"}</p>
                </div>
              </div>
            ) : results.length === 0 ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-card">
                <p className="text-lg font-bold text-ink-700">{ar ? "لم يتم العثور على برامج مطابقة" : "No matching programs found"}</p>
                <p className="mt-2 text-sm text-ink-500">{ar ? "جرّب تغيير القطاع أو المرحلة." : "Try changing the industry or stage."}</p>
              </div>
            ) : (
              <div className="space-y-4">
                <h2 className="text-lg font-bold text-ink-900">{ar ? `${results.length} برامج مطابقة` : `${results.length} matching programs`}</h2>
                {results.map((r) => (
                  <article key={r.program} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-bold text-ink-900">{r.name}</h3>
                        <p className="mt-1 text-sm text-ink-600">{r.program}</p>
                      </div>
                      <div className="text-end">
                        <span className="text-2xl font-bold text-brand-600">{r.score_percent}%</span>
                        <p className="text-xs text-ink-500">{ar ? "نسبة المطابقة" : "Match score"}</p>
                      </div>
                    </div>

                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400" style={{ width: `${r.score_percent}%` }} />
                    </div>

                    {r.reasons.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs font-bold text-ink-600">{ar ? "أسباب المطابقة" : "Match reasons"}</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {r.reasons.map((reason, i) => <Badge key={i} variant="success">{reason}</Badge>)}
                        </div>
                      </div>
                    )}

                    {r.missing.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-bold text-ink-600">{ar ? "متطلبات ناقصة" : "Missing requirements"}</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {r.missing.map((m, i) => <Badge key={i} variant="warning">{m}</Badge>)}
                        </div>
                      </div>
                    )}
                  </article>
                ))}

                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-xs text-amber-800">
                    {ar
                      ? "⚠️ النتائج استرشادية ولا تعني الأهلية المضمونة. تحقق من الموقع الرسمي لكل برنامج."
                      : "⚠️ Results are indicative and do not guarantee eligibility. Check each program's official website."}
                  </p>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
