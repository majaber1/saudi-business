"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { API_BASE } from "@/lib/api";

type Franchise = {
  id: number;
  brand: string;
  description_en?: string | null;
  description_ar?: string | null;
  sector: string;
  country?: string | null;
  regions: string[];
  investment_min?: number | null;
  investment_max?: number | null;
  franchise_fee?: number | null;
  royalty_model?: string | null;
  application_url?: string | null;
  source_url?: string | null;
  verification_status: string;
};

function money(value: number) {
  return new Intl.NumberFormat("en-SA", { style: "currency", currency: "SAR", maximumFractionDigits: 0 }).format(value);
}

export default function FranchiseServicePage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [franchises, setFranchises] = useState<Franchise[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(API_BASE + "/franchises/")
      .then((r) => r.json())
      .then(setFranchises)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="🏪"
        title={ar ? "الامتياز التجاري" : "Franchise"}
        subtitle={ar ? "استعرض فرص الامتياز التجاري المتاحة في السوق السعودي" : "Explore franchise opportunities available in the Saudi market"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}
          </div>
        ) : franchises.length === 0 ? (
          <EmptyState
            icon="🏪"
            title={ar ? "لا توجد فرص امتياز حاليًا" : "No franchise opportunities currently"}
            description={ar ? "سيتم إضافة فرص الامتياز قريبًا. تابعنا للتحديثات." : "Franchise opportunities will be added soon. Stay tuned for updates."}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {franchises.map((f) => (
              <article key={f.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover">
                <h3 className="text-lg font-bold text-ink-900">{f.brand}</h3>
                <p className="mt-2 text-sm text-ink-600 line-clamp-2">{ar ? f.description_ar : f.description_en}</p>
                <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-sm">
                  <div className="flex justify-between"><span className="text-ink-500">{ar ? "القطاع" : "Sector"}</span><span className="font-medium text-ink-700">{f.sector}</span></div>
                  {f.investment_min && <div className="flex justify-between"><span className="text-ink-500">{ar ? "الاستثمار" : "Investment"}</span><span className="font-medium text-ink-700">{money(f.investment_min)}{f.investment_max ? ` — ${money(f.investment_max)}` : ""}</span></div>}
                  {f.franchise_fee && <div className="flex justify-between"><span className="text-ink-500">{ar ? "رسوم الامتياز" : "Franchise fee"}</span><span className="font-medium text-ink-700">{money(f.franchise_fee)}</span></div>}
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <Badge variant={f.verification_status === "verified" ? "success" : "neutral"}>
                    {f.verification_status === "verified" ? (ar ? "موثّق" : "Verified") : (ar ? "عرض توضيحي" : "Demo")}
                  </Badge>
                  {f.regions.length > 0 && <Badge variant="info">{f.regions.join(", ")}</Badge>}
                </div>
              </article>
            ))}
          </div>
        )}

        <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm text-amber-800">
            {ar
              ? "⚠️ المعلومات المعروضة استرشادية. تحقق من المصدر الرسمي قبل اتخاذ أي قرار."
              : "⚠️ Information shown is indicative. Verify with official sources before making any decisions."}
          </p>
        </section>
      </div>
    </div>
  );
}
