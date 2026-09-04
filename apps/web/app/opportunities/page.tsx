"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import {
  listVerifiedOpportunities,
  getVerifiedOpportunity,
  compareVerifiedOpportunities,
  createStudyFromOpportunity,
  getToken,
  type VerifiedOpportunity,
  type OpportunityComparisonItem,
} from "@/lib/api";

const SECTOR_OPTIONS = [
  { value: "", label_ar: "جميع القطاعات", label_en: "All Sectors" },
  { value: "food_beverage", label_ar: "أغذية ومشروبات ومقاهي", label_en: "Food & Beverage / Coffee" },
  { value: "manufacturing", label_ar: "صناعات تحويلية وتعبئة", label_en: "Manufacturing & Packaging" },
  { value: "logistics", label_ar: "خدمات لوجستية وتخزين مبرد", label_en: "Logistics & Cold Storage" },
  { value: "agriculture", label_ar: "زراعة وتقنيات مائية حديثة", label_en: "Agriculture & Agritech" },
  { value: "industrial", label_ar: "صناعة وتدوير بيئي", label_en: "Industrial & Recycling" },
  { value: "sports_entertainment", label_ar: "رياضة وترفيه ولياقة", label_en: "Sports & Fitness" },
  { value: "retail", label_ar: "تجزئة ورعاية متخصصة", label_en: "Specialty Retail" },
  { value: "services", label_ar: "خدمات وبنية تحتية مشتركة", label_en: "Services & Shared Infra" },
];

const GEOGRAPHY_OPTIONS = [
  { value: "", label_ar: "جميع المناطق", label_en: "All Regions" },
  { value: "KSA_NATIONAL", label_ar: "تغطية وطنية شاملة", label_en: "KSA Nationwide" },
  { value: "RIYADH", label_ar: "منطقة الرياض", label_en: "Riyadh Region" },
  { value: "WESTERN", label_ar: "المنطقة الغربية (مكة / جدة)", label_en: "Western Region" },
  { value: "EASTERN", label_ar: "المنطقة الشرقية", label_en: "Eastern Region" },
  { value: "QASSIM", label_ar: "منطقة القصيم", label_en: "Al-Qassim Region" },
];

function fmtSAR(n: number | null | undefined, locale: "ar" | "en") {
  if (n === null || n === undefined) return locale === "ar" ? "غير معلن" : "Unspecified";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n) + (locale === "ar" ? " ر.س" : " SAR");
}

export default function OpportunitiesPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const router = useRouter();

  // Active view tab: "all" | "BUSINESS_OPPORTUNITY" | "FRANCHISE" | "compare"
  const [activeTab, setActiveTab] = useState<"all" | "BUSINESS_OPPORTUNITY" | "FRANCHISE" | "compare">("all");

  // Filter states
  const [sector, setSector] = useState("");
  const [geography, setGeography] = useState("");
  const [budget, setBudget] = useState<string>("");
  const [search, setSearch] = useState("");

  // Data states
  const [items, setItems] = useState<VerifiedOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Selection for comparison (max 4)
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [comparisonItems, setComparisonItems] = useState<OpportunityComparisonItem[]>([]);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Detail Modal state
  const [detailItem, setDetailItem] = useState<VerifiedOpportunity | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Study Modal state
  const [targetForStudy, setTargetForStudy] = useState<VerifiedOpportunity | null>(null);
  const [studyTitle, setStudyTitle] = useState("");
  const [customBudget, setCustomBudget] = useState<string>("");
  const [creatingStudy, setCreatingStudy] = useState(false);
  const [createStudyError, setCreateStudyError] = useState("");

  // Fetch opportunities matching current filters
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    const parsedBudget = parseFloat(budget);
    const filterType = activeTab === "all" || activeTab === "compare" ? undefined : activeTab;

    listVerifiedOpportunities({
      type: filterType,
      sector: sector || undefined,
      geography: geography || undefined,
      max_budget: !Number.isNaN(parsedBudget) && parsedBudget > 0 ? parsedBudget : undefined,
      search: search.trim() || undefined,
    })
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeTab, sector, geography, budget, search]);

  // Load comparison data when compare tab is opened or selectedIds change
  useEffect(() => {
    if (activeTab === "compare" && selectedIds.length > 0) {
      setComparisonLoading(true);
      compareVerifiedOpportunities(selectedIds)
        .then(setComparisonItems)
        .catch(() => setComparisonItems([]))
        .finally(() => setComparisonLoading(false));
    }
  }, [activeTab, selectedIds]);

  // Comparison toggle
  const toggleComparison = (id: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      if (prev.length >= 4) {
        alert(ar ? "يمكنك مقارنة 4 فرص كحد أقصى في وقت واحد" : "You can compare up to 4 opportunities simultaneously");
        return prev;
      }
      return [...prev, id];
    });
  };

  // Open detail view
  const openDetail = async (id: number) => {
    setDetailLoading(true);
    try {
      const data = await getVerifiedOpportunity(id);
      setDetailItem(data);
    } catch {
      const fallback = items.find((i) => i.id === id);
      if (fallback) setDetailItem(fallback);
    } finally {
      setDetailLoading(false);
    }
  };

  // Prepare create study modal
  const openCreateStudy = (opp: VerifiedOpportunity) => {
    const token = getToken();
    if (!token) {
      router.push(`/login?next=${encodeURIComponent("/opportunities")}`);
      return;
    }
    setTargetForStudy(opp);
    setStudyTitle(ar ? (opp.brand_name ? `دراسة امتياز: ${opp.brand_name}` : `دراسة: ${opp.title_ar}`) : `Study: ${opp.title_en}`);
    setCustomBudget(opp.investment_min ? String(opp.investment_min) : "250000");
    setCreateStudyError("");
  };

  // Execute create study
  const handleConfirmCreateStudy = async () => {
    if (!targetForStudy) return;
    const token = getToken();
    if (!token) {
      router.push(`/login?next=${encodeURIComponent("/opportunities")}`);
      return;
    }

    setCreatingStudy(true);
    setCreateStudyError("");

    try {
      const parsedBudget = parseFloat(customBudget);
      const res = await createStudyFromOpportunity(token, targetForStudy.id, {
        study_title: studyTitle.trim() || undefined,
        custom_budget: !Number.isNaN(parsedBudget) && parsedBudget > 0 ? parsedBudget : undefined,
      });

      // Navigate to the newly created study workspace!
      router.push(`/projects/${res.project_id}/studies/${res.study_id}`);
    } catch (err) {
      setCreateStudyError(err instanceof Error ? err.message : String(err));
      setCreatingStudy(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8faf9] pb-24 pt-8 text-slate-900">
      <div className="container-page">
        {/* Header / Hero */}
        <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                  {ar ? "الموجة 3: سجل الفرص والامتياز الموثق" : "Wave 3: Verified Opportunity Registry"}
                </span>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  {ar ? "بيانات حقيقية بمصدر رسمي" : "Authentic Sourced Data"}
                </span>
              </div>
              <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                {ar ? "مركز الفرص الاستثمارية والامتياز التجاري" : "Opportunities & Franchise Center"}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
                {ar
                  ? "استكشف الفرص الاستثمارية وعلامات الامتياز التجاري المعتمدة في المملكة العربية السعودية. جميع البيانات مستمدة مباشرة من بوابات رسمية (.gov.sa) وإفصاحات العلامات التجارية دون أي افتراضات أو أرقام غير موثقة."
                  : "Explore verified business and franchise opportunities in Saudi Arabia. Sourced directly from official portals (.gov.sa) and franchisor disclosures with zero fabricated financials."}
              </p>
            </div>

            {/* Selection Tray Indicator */}
            {selectedIds.length > 0 && (
              <div className="flex items-center gap-3 rounded-2xl border border-brand-200 bg-brand-50 p-4">
                <div>
                  <p className="text-xs font-medium text-brand-900">
                    {ar ? `محدد للمقارنة: ${selectedIds.length} فرصة` : `${selectedIds.length} selected to compare`}
                  </p>
                  <p className="text-[11px] text-brand-700">{ar ? "مقارنة موضوعية مبنية على الحقائق" : "Fact-based side-by-side"}</p>
                </div>
                <button
                  onClick={() => setActiveTab("compare")}
                  className="rounded-xl bg-brand-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-brand-700"
                >
                  {ar ? "فتح جدول المقارنة" : "View Comparison"}
                </button>
                <button
                  onClick={() => setSelectedIds([])}
                  className="text-xs text-slate-500 hover:text-slate-800"
                >
                  {ar ? "إلغاء" : "Clear"}
                </button>
              </div>
            )}
          </div>

          {/* Official Provenance Badges Banner */}
          <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
            <span className="font-medium text-slate-700">{ar ? "الجهات المرجعية الرسمية:" : "Official Source Authorities:"}</span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">الهيئة العامة للمنشآت (منشآت)</span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">استثمر في السعودية (وزارة الاستثمار)</span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">مركز الامتياز التجاري السعودي</span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">صندوق التنمية الزراعية (ADF)</span>
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-slate-700">المركز الوطني لإدارة النفايات (موان)</span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="mt-6 flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab("all")}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
              activeTab === "all" ? "bg-slate-900 text-white shadow-sm" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            {ar ? "جميع الفرص والامتياز" : "All Opportunities"}
          </button>
          <button
            onClick={() => setActiveTab("BUSINESS_OPPORTUNITY")}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
              activeTab === "BUSINESS_OPPORTUNITY" ? "bg-slate-900 text-white shadow-sm" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            {ar ? "الفرص التجارية والصناعية" : "Business Opportunities"}
          </button>
          <button
            onClick={() => setActiveTab("FRANCHISE")}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
              activeTab === "FRANCHISE" ? "bg-slate-900 text-white shadow-sm" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            {ar ? "فرص الامتياز التجاري (الفرانشايز)" : "Franchise Brands"}
          </button>
          {selectedIds.length > 0 && (
            <button
              onClick={() => setActiveTab("compare")}
              className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                activeTab === "compare" ? "bg-brand-700 text-white shadow-sm" : "bg-brand-50 text-brand-800 hover:bg-brand-100"
              }`}
            >
              {ar ? `المقارنة المباشرة (${selectedIds.length})` : `Side-by-side Compare (${selectedIds.length})`}
            </button>
          )}
        </div>

        {/* Comparison View */}
        {activeTab === "compare" ? (
          <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {ar ? "المقارنة الموضوعية المباشرة" : "Factual Side-by-Side Comparison"}
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  {ar ? "مقارنة مبنية على الحقول الموثقة من المصدر الرسمي حصراً دون نقاط ترجيح اصطناعية" : "Strict comparison of verified source fields with zero artificial scoring"}
                </p>
              </div>
              <button
                onClick={() => setActiveTab("all")}
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
              >
                {ar ? "العودة للقائمة" : "Back to List"}
              </button>
            </div>

            {comparisonLoading ? (
              <div className="py-16 text-center text-sm text-slate-500">{ar ? "جارٍ إعداد جدول المقارنة..." : "Loading comparison..."}</div>
            ) : comparisonItems.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-500">
                {ar ? "لم يتم تحديد أي فرص للمقارنة. حدد فرصة واحدة أو أكثر من القائمة." : "No opportunities selected for comparison."}
              </div>
            ) : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full border-collapse text-right text-xs sm:text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50 text-slate-700">
                      <th className="p-3 font-semibold">{ar ? "المعيار" : "Attribute"}</th>
                      {comparisonItems.map((item) => (
                        <th key={item.id} className="min-w-[220px] p-3 font-semibold text-slate-900">
                          <div className="flex items-center justify-between gap-2">
                            <span>{ar ? item.title_ar : item.title_en}</span>
                            <button
                              onClick={() => toggleComparison(item.id)}
                              className="text-xs text-red-500 hover:underline"
                              title={ar ? "إزالة من المقارنة" : "Remove"}
                            >
                              ✕
                            </button>
                          </div>
                          {item.brand_name && (
                            <span className="mt-1 block text-xs font-normal text-brand-700">{item.brand_name}</span>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "نوع الفرصة" : "Type"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 font-medium text-slate-800">
                          {i.opportunity_type === "FRANCHISE" ? (ar ? "امتياز تجاري" : "Franchise") : (ar ? "فرصة استثمارية" : "Business Opportunity")}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "القطاع" : "Sector"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-slate-700">{i.sector}</td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "النطاق الجغرافي" : "Geography"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-slate-700">
                          {i.city ? `${i.city} (${i.region || ""})` : (ar ? "تغطية وطنية شاملة" : "Nationwide")}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "نطاق الاستثمار المنشور" : "Published Investment"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 font-mono text-slate-800">
                          {fmtSAR(i.investment_min, locale)} – {fmtSAR(i.investment_max, locale)}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "رسوم الامتياز (الفرانشايز)" : "Franchise Fee"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-slate-700">
                          {i.franchise_fee ? fmtSAR(i.franchise_fee, locale) : (ar ? "غير منطبق / غير معلن" : "N/A")}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "نموذج الإتاوة والملكية" : "Royalty Model"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-xs text-slate-700">{i.royalty_model || "—"}</td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "المساحة التشغيلية المطلوبة" : "Required Space"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-slate-700">{i.required_space || "—"}</td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "جهة المصدر الرسمي" : "Source Owner"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3 text-xs text-slate-700">
                          <a
                            href={i.official_source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-brand-700 hover:underline"
                          >
                            {i.source_owner} ↗
                          </a>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "حالة التوثيق" : "Verification Status"}</td>
                      {comparisonItems.map((i) => (
                        <td key={i.id} className="p-3">
                          <span className="inline-block rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                            {i.verification_status}
                          </span>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="bg-slate-50/50 p-3 font-medium text-slate-600">{ar ? "إجراء اتخاذ القرار" : "Action"}</td>
                      {comparisonItems.map((i) => {
                        const original = items.find((o) => o.id === i.id);
                        return (
                          <td key={i.id} className="p-3">
                            <button
                              onClick={() => {
                                if (original) openCreateStudy(original);
                              }}
                              className="w-full rounded-xl bg-brand-600 px-3 py-2 text-xs font-semibold text-white hover:bg-brand-700"
                            >
                              {ar ? "إنشاء دراسة جدوى" : "Create Study"}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Filters Bar */}
            <div className="mt-6 grid gap-4 rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="block text-xs font-medium text-slate-700">{ar ? "القطاع الاستثماري" : "Sector"}</label>
                <select
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-medium text-slate-800 outline-none focus:border-brand-500 focus:bg-white"
                >
                  {SECTOR_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {ar ? s.label_ar : s.label_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700">{ar ? "النطاق الجغرافي" : "Geography"}</label>
                <select
                  value={geography}
                  onChange={(e) => setGeography(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-medium text-slate-800 outline-none focus:border-brand-500 focus:bg-white"
                >
                  {GEOGRAPHY_OPTIONS.map((g) => (
                    <option key={g.value} value={g.value}>
                      {ar ? g.label_ar : g.label_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700">{ar ? "ميزانيتي المتاحة (ر.س)" : "Available Budget (SAR)"}</label>
                <input
                  type="number"
                  min={0}
                  placeholder={ar ? "مثال: 500,000" : "e.g. 500,000"}
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-medium text-slate-800 outline-none focus:border-brand-500 focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700">{ar ? "بحث بالاسم أو العلامة" : "Search"}</label>
                <input
                  type="text"
                  placeholder={ar ? "اكتب للبحث..." : "Search..."}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-medium text-slate-800 outline-none focus:border-brand-500 focus:bg-white"
                />
              </div>
            </div>

            {/* Opportunities List */}
            {loading ? (
              <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-64 animate-pulse rounded-3xl border border-slate-200 bg-white" />
                ))}
              </div>
            ) : error ? (
              <div className="mt-8 rounded-2xl bg-red-50 p-6 text-center text-sm text-red-700">{error}</div>
            ) : items.length === 0 ? (
              <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-600">
                {ar ? "لا توجد فرص مطابقة للشروط المحددة حالياً." : "No matching opportunities found."}
              </div>
            ) : (
              <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((opp) => {
                  const isCompared = selectedIds.includes(opp.id);
                  const isFranchise = opp.opportunity_type === "FRANCHISE";

                  return (
                    <div
                      key={opp.id}
                      className="flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                    >
                      <div>
                        {/* Badges */}
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              isFranchise ? "bg-purple-100 text-purple-800" : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {isFranchise ? (ar ? "امتياز تجاري" : "Franchise") : (ar ? "فرصة استثمارية" : "Business Opp")}
                          </span>
                          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-600">
                            {opp.verification_status}
                          </span>
                        </div>

                        {/* Title & Brand */}
                        <h3 className="mt-3 text-base font-bold text-slate-900">
                          {ar ? opp.title_ar : opp.title_en}
                        </h3>
                        {opp.brand_name && (
                          <p className="mt-0.5 text-xs font-semibold text-brand-700">{opp.brand_name}</p>
                        )}
                        <p className="mt-1 text-xs text-slate-500">
                          {opp.sector} {opp.city ? `· ${opp.city}` : ""}
                        </p>

                        {/* Description excerpt */}
                        <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-slate-600">
                          {ar ? opp.description_ar : opp.description_en}
                        </p>

                        {/* Financial and Requirements Facts */}
                        <div className="mt-5 space-y-2 rounded-2xl bg-slate-50/80 p-3.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500">{ar ? "الاستثمار التقديري:" : "Est. Investment:"}</span>
                            <span className="font-mono font-medium text-slate-900">
                              {opp.investment_min
                                ? `${fmtSAR(opp.investment_min, locale)} – ${fmtSAR(opp.investment_max, locale)}`
                                : (ar ? "غير معلن - يحدده المستثمر" : "Unspecified")}
                            </span>
                          </div>

                          {isFranchise && opp.franchise_fee !== null && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500">{ar ? "رسوم الامتياز:" : "Franchise Fee:"}</span>
                              <span className="font-mono font-medium text-slate-900">{fmtSAR(opp.franchise_fee, locale)}</span>
                            </div>
                          )}

                          {opp.required_space && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500">{ar ? "المساحة التشغيلية:" : "Space:"}</span>
                              <span className="text-slate-800">{opp.required_space}</span>
                            </div>
                          )}

                          <div className="flex items-center justify-between border-t border-slate-200/60 pt-1.5 text-[11px]">
                            <span className="text-slate-500">{ar ? "المصدر الرسمي:" : "Source:"}</span>
                            <span className="truncate text-slate-700" title={opp.source_owner}>
                              {opp.source_owner}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="mt-5 border-t border-slate-100 pt-4">
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => openDetail(opp.id)}
                            className="rounded-xl border border-slate-200 bg-white py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50"
                          >
                            {ar ? "التفاصيل والأدلة" : "Details & Evidence"}
                          </button>
                          <button
                            onClick={() => openCreateStudy(opp)}
                            className="rounded-xl bg-brand-600 py-2 text-xs font-semibold text-white shadow-sm hover:bg-brand-700"
                          >
                            {ar ? "إنشاء دراسة جدوى" : "Create Study"}
                          </button>
                        </div>

                        <div className="mt-2.5 flex items-center justify-between text-xs">
                          <button
                            onClick={() => toggleComparison(opp.id)}
                            className={`text-[11px] font-medium transition ${
                              isCompared ? "font-bold text-brand-700" : "text-slate-500 hover:text-slate-800"
                            }`}
                          >
                            {isCompared ? (ar ? "✓ مضاف للمقارنة" : "✓ In Compare") : (ar ? "+ إضافة للمقارنة" : "+ Add to Compare")}
                          </button>

                          <a
                            href={opp.official_source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-slate-400 hover:text-slate-700 hover:underline"
                          >
                            {ar ? "رابط المصدر ↗" : "Official Link ↗"}
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* DETAIL MODAL / DRAWER */}
        {detailItem && (
          <div
            role="dialog"
            aria-modal="true"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
          >
            <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
              <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-semibold text-purple-800">
                      {detailItem.opportunity_type === "FRANCHISE" ? (ar ? "امتياز تجاري" : "Franchise") : (ar ? "فرصة استثمارية" : "Business Opportunity")}
                    </span>
                    <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                      {detailItem.verification_status}
                    </span>
                  </div>
                  <h2 className="mt-2 text-xl font-bold text-slate-900">
                    {ar ? detailItem.title_ar : detailItem.title_en}
                  </h2>
                  {detailItem.brand_name && (
                    <p className="text-sm font-semibold text-brand-700">{detailItem.brand_name}</p>
                  )}
                </div>
                <button
                  onClick={() => setDetailItem(null)}
                  className="grid h-8 w-8 place-items-center rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200"
                >
                  ✕
                </button>
              </div>

              {/* Description */}
              <div className="mt-4">
                <p className="text-xs leading-relaxed text-slate-700">
                  {ar ? detailItem.description_ar : detailItem.description_en}
                </p>
              </div>

              {/* Verified Facts vs Unknowns Breakdown */}
              <div className="mt-6 space-y-4">
                <h3 className="text-sm font-bold text-slate-900">
                  {ar ? "تصنيف الحقائق والمعلومات (منهجية عدم التزييف)" : "Facts Classification"}
                </h3>

                <div className="grid gap-3 sm:grid-cols-2">
                  {/* Published Facts */}
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900">
                      <span>✓</span>
                      <span>{ar ? "معلومات منشورة وموثقة" : "Published Facts"}</span>
                    </div>
                    <ul className="mt-2 space-y-1.5 text-xs text-emerald-950">
                      {detailItem.facts_breakdown?.published_facts?.map((fact, idx) => (
                        <li key={idx} className="list-inside list-disc">{fact}</li>
                      )) || <li className="text-slate-400">—</li>}
                    </ul>
                  </div>

                  {/* Platform Normalized Facts */}
                  <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-4">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-blue-900">
                      <span>ℹ</span>
                      <span>{ar ? "تصنيف المنصة المعياري" : "Platform-Normalized Facts"}</span>
                    </div>
                    <ul className="mt-2 space-y-1.5 text-xs text-blue-950">
                      {detailItem.facts_breakdown?.platform_normalized_facts?.map((fact, idx) => (
                        <li key={idx} className="list-inside list-disc">{fact}</li>
                      )) || <li className="text-slate-400">—</li>}
                    </ul>
                  </div>

                  {/* Unknown / Missing Info */}
                  <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-4">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                      <span>?</span>
                      <span>{ar ? "معلومات غير معلنة (تبقى غير معلنة)" : "Unknown / Unannounced Info"}</span>
                    </div>
                    <ul className="mt-2 space-y-1.5 text-xs text-amber-950">
                      {detailItem.facts_breakdown?.unknowns?.map((fact, idx) => (
                        <li key={idx} className="list-inside list-disc">{fact}</li>
                      )) || <li className="text-slate-400">—</li>}
                    </ul>
                  </div>

                  {/* User Assumptions Needed */}
                  <div className="rounded-2xl border border-purple-200 bg-purple-50/50 p-4">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-purple-900">
                      <span>✎</span>
                      <span>{ar ? "افتراضات مطلوبة من المستثمر" : "User Assumptions Needed"}</span>
                    </div>
                    <ul className="mt-2 space-y-1.5 text-xs text-purple-950">
                      {detailItem.facts_breakdown?.user_assumptions_needed?.map((fact, idx) => (
                        <li key={idx} className="list-inside list-disc">{fact}</li>
                      )) || <li className="text-slate-400">—</li>}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Provenance and Evidence Details */}
              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs">
                <h4 className="font-bold text-slate-800">{ar ? "بيانات السجل وتوثيق المصدر:" : "Source Provenance:"}</h4>
                <div className="mt-3 grid gap-2 text-slate-600 sm:grid-cols-2">
                  <div>
                    <span className="font-medium text-slate-700">{ar ? "الجهة المصدرية:" : "Source Owner:"} </span>
                    {detailItem.source_owner}
                  </div>
                  <div>
                    <span className="font-medium text-slate-700">{ar ? "نوع التوثيق:" : "Source Type:"} </span>
                    {detailItem.source_type}
                  </div>
                  <div>
                    <span className="font-medium text-slate-700">{ar ? "إصدار البيانات:" : "Data Version:"} </span>
                    {detailItem.data_version}
                  </div>
                  <div>
                    <span className="font-medium text-slate-700">{ar ? "آخر تحقق رسمي:" : "Last Verified:"} </span>
                    {detailItem.last_verified_at?.slice(0, 10)}
                  </div>
                  <div className="sm:col-span-2">
                    <span className="font-medium text-slate-700">{ar ? "رابط المصدر:" : "Official URL:"} </span>
                    <a
                      href={detailItem.official_source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="break-all text-brand-700 hover:underline"
                    >
                      {detailItem.official_source_url}
                    </a>
                  </div>
                </div>

                {detailItem.source_evidence && (
                  <div className="mt-3 border-t border-slate-200/60 pt-2 text-[11px] text-slate-600">
                    <p className="font-medium text-slate-700">{ar ? "مقتطف التوثيق المرجعي:" : "Source Quotation:"}</p>
                    <p className="mt-1 italic">
                      &ldquo;{String(detailItem.source_evidence.quote_ar || detailItem.source_evidence.report_ref || "")}&rdquo;
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Actions */}
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
                <button
                  onClick={() => setDetailItem(null)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  {ar ? "إغلاق" : "Close"}
                </button>
                <button
                  onClick={() => {
                    const target = detailItem;
                    setDetailItem(null);
                    openCreateStudy(target);
                  }}
                  className="rounded-xl bg-brand-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-brand-700"
                >
                  {ar ? "إنشاء دراسة جدوى من هذه الفرصة" : "Create Study from this Opportunity"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* CREATE STUDY MODAL */}
        {targetForStudy && (
          <div
            role="dialog"
            aria-modal="true"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
          >
            <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
              <h3 className="text-xl font-bold text-slate-900">
                {ar ? "إنشاء دراسة جدوى من فرصة حقيقية" : "Create Feasibility Study from Opportunity"}
              </h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-600">
                {ar
                  ? "سيتم إنشاء مساحة مشروع ودراسة جدوى حقيقية دائمة، مع نقل البيانات الموثقة من المصدر وحفظ سلسلة الأصل والتوثيق (Lineage) دون أي أرقام مفبركة."
                  : "A persistent study will be initialized with immutable source lineage and verified facts transferred."}
              </p>

              <div className="mt-5 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    {ar ? "عنوان الدراسة" : "Study Title"}
                  </label>
                  <input
                    type="text"
                    value={studyTitle}
                    onChange={(e) => setStudyTitle(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 text-xs outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    {ar ? "الميزانية المبدئية المقترحة (ر.س)" : "Proposed Investment Budget (SAR)"}
                    <span className="mx-1 text-[11px] font-normal text-slate-500">
                      {targetForStudy.investment_min
                        ? (ar ? "(مأخوذ من المصدر الرسمي كحد أدنى)" : "(from verified source minimum)")
                        : (ar ? "(افتراض مستخدم - لم يُنشر في المصدر)" : "(user assumption)")}
                    </span>
                  </label>
                  <input
                    type="number"
                    min={10000}
                    value={customBudget}
                    onChange={(e) => setCustomBudget(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-mono text-xs outline-none focus:border-brand-500"
                  />
                </div>

                <div className="rounded-2xl bg-slate-50 p-3 text-xs text-slate-600">
                  <p className="font-semibold text-slate-800">{ar ? "الحقائق المنقولة رسمياً:" : "Transferred Lineage:"}</p>
                  <p className="mt-1 text-[11px]">
                    {ar ? "القطاع:" : "Sector:"} {targetForStudy.sector} · {ar ? "المصدر:" : "Source:"} {targetForStudy.source_owner} · {ar ? "الإصدار:" : "Version:"} {targetForStudy.data_version}
                  </p>
                </div>

                {createStudyError && (
                  <p role="alert" className="rounded-xl bg-red-50 p-3 text-xs text-red-700">{createStudyError}</p>
                )}
              </div>

              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
                <button
                  onClick={() => setTargetForStudy(null)}
                  disabled={creatingStudy}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  {ar ? "إلغاء" : "Cancel"}
                </button>
                <button
                  onClick={handleConfirmCreateStudy}
                  disabled={creatingStudy}
                  className="rounded-xl bg-brand-600 px-5 py-2.5 text-xs font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-50"
                >
                  {creatingStudy ? (ar ? "جارٍ إنشاء الدراسة..." : "Creating Study...") : (ar ? "تأكيد وبدء الدراسة" : "Confirm & Launch Study")}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
