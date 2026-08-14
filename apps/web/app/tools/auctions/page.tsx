"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { API_BASE } from "@/lib/api";

type Auction = {
  id: number;
  title: string;
  category: string;
  description?: string | null;
  asking_price?: number | null;
  starts_at?: string | null;
  ends_at?: string | null;
  status: string;
};

function money(value: number) {
  return new Intl.NumberFormat("en-SA", { style: "currency", currency: "SAR", maximumFractionDigits: 0 }).format(value);
}

export default function AuctionsServicePage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(API_BASE + "/auctions/")
      .then((r) => r.json())
      .then(setAuctions)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const statusBadge = (s: string) => {
    if (s === "active") return <Badge variant="success">{ar ? "نشط" : "Active"}</Badge>;
    if (s === "ended") return <Badge variant="neutral">{ar ? "انتهى" : "Ended"}</Badge>;
    return <Badge variant="warning">{ar ? "مسودة" : "Draft"}</Badge>;
  };

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="🔨"
        title={ar ? "المزادات" : "Auctions"}
        subtitle={ar ? "تصفّح مزادات الأعمال والأصول التجارية" : "Browse business and commercial asset auctions"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}
          </div>
        ) : auctions.length === 0 ? (
          <EmptyState
            icon="🔨"
            title={ar ? "لا توجد مزادات حاليًا" : "No auctions currently"}
            description={ar ? "سيتم إضافة المزادات قريبًا. تابعنا للتحديثات." : "Auctions will be added soon. Stay tuned for updates."}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {auctions.map((a) => (
              <article key={a.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-lg font-bold text-ink-900">{a.title}</h3>
                  {statusBadge(a.status)}
                </div>
                <p className="mt-2 text-sm text-ink-600 line-clamp-2">{a.description}</p>
                <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-sm">
                  <div className="flex justify-between"><span className="text-ink-500">{ar ? "الفئة" : "Category"}</span><span className="font-medium text-ink-700">{a.category}</span></div>
                  {a.asking_price && <div className="flex justify-between"><span className="text-ink-500">{ar ? "السعر" : "Price"}</span><span className="font-bold text-brand-600">{money(a.asking_price)}</span></div>}
                  {a.ends_at && <div className="flex justify-between"><span className="text-ink-500">{ar ? "ينتهي" : "Ends"}</span><span className="font-medium text-ink-700">{new Date(a.ends_at).toLocaleDateString(ar ? "ar-SA" : "en-SA")}</span></div>}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
