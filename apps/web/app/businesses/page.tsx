"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { getToken, listProjects, type Project } from "@/lib/api";

function money(value: number, locale: "ar" | "en") {
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

const stageBadge = (stage: string, ar: boolean) => {
  const labels: Record<string, { ar: string; en: string; variant: "success" | "warning" | "info" | "neutral" }> = {
    idea: { ar: "فكرة", en: "Idea", variant: "info" },
    mvp: { ar: "منتج أولي", en: "MVP", variant: "warning" },
    active: { ar: "نشط", en: "Active", variant: "success" },
    review: { ar: "قيد المراجعة", en: "Under Review", variant: "warning" },
    draft: { ar: "مسودة", en: "Draft", variant: "neutral" },
  };
  const l = labels[stage] || labels.draft;
  return <Badge variant={l.variant}>{ar ? l.ar : l.en}</Badge>;
};

export default function BusinessesPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    setSignedIn(true);
    listProjects(token, true)
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const active = projects.filter((p) => !p.is_archived);
  const archived = projects.filter((p) => p.is_archived);

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="🏢"
        title={ar ? "أعمالي" : "My Businesses"}
        subtitle={ar ? "مشاريعك وسياقك التجاري المشترك بين جميع الأدوات" : "Your projects and shared business context across all tools"}
        actions={
          signedIn ? (
            <Link
              href="/projects"
              className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-card transition hover:bg-brand-700"
            >
              {ar ? "إضافة مشروع جديد" : "Add new project"}
            </Link>
          ) : undefined
        }
      />

      <div className="container-page py-8">
        {!signedIn ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-card">
            <span className="mb-4 inline-block text-5xl">🔐</span>
            <h2 className="text-xl font-bold text-ink-900">{ar ? "سجّل الدخول لعرض مشاريعك" : "Sign in to view your projects"}</h2>
            <p className="mt-2 text-sm text-ink-600">{ar ? "مشاريعك تربط جميع أدوات المنصة ببيانات موحدة." : "Your projects link all platform tools with unified data."}</p>
            <Link href="/login" className="mt-6 inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-card">{ar ? "تسجيل الدخول" : "Sign in"}</Link>
          </div>
        ) : loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}
          </div>
        ) : active.length === 0 ? (
          <EmptyState
            icon="🏢"
            title={ar ? "لا توجد مشاريع بعد" : "No projects yet"}
            description={ar ? "أنشئ مشروعك الأول لربط جميع أدواتك بسياق تجاري موحّد." : "Create your first project to link all your tools with a unified business context."}
            actionLabel={ar ? "إنشاء مشروع" : "Create project"}
            actionHref="/projects"
          />
        ) : (
          <>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {active.map((p) => (
                <Link key={p.id} href={`/businesses/${p.id}`}>
                  <article className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card-hover">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-lg font-bold text-ink-900 group-hover:text-brand-700">{p.name}</h3>
                      {stageBadge(p.stage, ar)}
                    </div>
                    <p className="mt-2 text-sm text-ink-600">{p.industry}</p>
                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
                      <span className="text-sm font-semibold text-ink-700">{money(Number(p.investment), locale as "ar" | "en")}</span>
                      <span className="text-xs text-ink-500">{new Date(p.created_at).toLocaleDateString(ar ? "ar-SA" : "en-SA")}</span>
                    </div>
                  </article>
                </Link>
              ))}
            </div>

            {archived.length > 0 && (
              <div className="mt-10">
                <h2 className="mb-4 text-lg font-bold text-ink-700">{ar ? "المشاريع المؤرشفة" : "Archived projects"}</h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {archived.map((p) => (
                    <article key={p.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-5 opacity-70">
                      <h3 className="font-semibold text-ink-700">{p.name}</h3>
                      <p className="mt-1 text-sm text-ink-500">{p.industry} — {money(Number(p.investment), locale as "ar" | "en")}</p>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
