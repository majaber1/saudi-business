"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { getToken, listStudies, reportDownloadUrl, type Study } from "@/lib/api";

const reportTypes = [
  { key: "feasibility", icon: "📊", ar: "تقرير دراسة الجدوى", en: "Feasibility Report" },
  { key: "executive", icon: "📋", ar: "ملخص تنفيذي", en: "Executive Summary" },
  { key: "financial", icon: "💰", ar: "تقرير مالي", en: "Financial Report" },
  { key: "investor", icon: "💼", ar: "حزمة المستثمر", en: "Investor Package" },
  { key: "qualification", icon: "✅", ar: "تقرير التأهيل", en: "Qualification Report" },
  { key: "funding", icon: "🏦", ar: "تقرير جاهزية التمويل", en: "Funding Readiness" },
];

export default function ReportsServicePage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [studies, setStudies] = useState<Study[]>([]);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) { setLoading(false); return; }
    setSignedIn(true);
    listStudies(token)
      .then(setStudies)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const completed = studies.filter((s) => s.status === "completed");

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="📄"
        title={ar ? "التقارير وحزمة المستثمر" : "Reports & Investor Package"}
        subtitle={ar ? "أنشئ تقارير احترافية من دراساتك وتحليلاتك" : "Generate professional reports from your studies and analyses"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
      />

      <div className="container-page space-y-8 py-8">
        <section className="rounded-2xl border border-brand-200 bg-white p-6 shadow-card sm:p-8">
          <h2 className="text-xl font-bold text-ink-900">{ar ? "أنواع التقارير" : "Report types"}</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {reportTypes.map((rt) => (
              <div key={rt.key} className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-5">
                <span className="mt-0.5 text-2xl">{rt.icon}</span>
                <p className="font-semibold text-ink-800">{ar ? rt.ar : rt.en}</p>
              </div>
            ))}
          </div>
        </section>

        {!signedIn ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-card">
            <h2 className="text-xl font-bold text-ink-900">{ar ? "سجّل الدخول لتنزيل التقارير" : "Sign in to download reports"}</h2>
            <p className="mt-2 text-sm text-ink-600">{ar ? "أكمل دراسة جدوى أولاً ثم قم بتصدير التقرير." : "Complete a feasibility study first, then export the report."}</p>
            <Link href="/login" className="mt-6 inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white">{ar ? "تسجيل الدخول" : "Sign in"}</Link>
          </div>
        ) : loading ? (
          <div className="h-32 animate-pulse rounded-2xl border border-slate-200 bg-white" />
        ) : completed.length === 0 ? (
          <EmptyState
            icon="📄"
            title={ar ? "لا توجد تقارير جاهزة" : "No reports ready"}
            description={ar ? "أكمل دراسة جدوى لتتمكن من تصدير التقرير." : "Complete a feasibility study to export a report."}
            actionLabel={ar ? "بدء دراسة" : "Start a study"}
            actionHref="/feasibility/new"
          />
        ) : (
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
            <header className="border-b border-slate-100 px-6 py-4">
              <h2 className="font-bold text-ink-900">{ar ? "الدراسات الجاهزة للتصدير" : "Studies ready for export"}</h2>
            </header>
            <div className="divide-y divide-slate-100">
              {completed.map((s) => (
                <div key={s.id} className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 transition hover:bg-slate-50">
                  <div>
                    <p className="font-semibold text-ink-900">{s.title}</p>
                    <p className="mt-1 text-xs text-ink-500">{s.study_type}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <a href={reportDownloadUrl(s.id, "pdf", "ar")} target="_blank" className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-bold text-ink-700 hover:border-brand-500 hover:text-brand-600">
                      PDF {ar ? "عربي" : "AR"}
                    </a>
                    <a href={reportDownloadUrl(s.id, "pdf", "en")} target="_blank" className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-bold text-ink-700 hover:border-brand-500 hover:text-brand-600">
                      PDF {ar ? "إنجليزي" : "EN"}
                    </a>
                    <a href={reportDownloadUrl(s.id, "docx", "ar")} target="_blank" className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-bold text-ink-700 hover:border-brand-500 hover:text-brand-600">
                      DOCX {ar ? "عربي" : "AR"}
                    </a>
                    <a href={reportDownloadUrl(s.id, "docx", "en")} target="_blank" className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-bold text-ink-700 hover:border-brand-500 hover:text-brand-600">
                      DOCX {ar ? "إنجليزي" : "EN"}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="rounded-2xl border border-gold-200 bg-gold-50 p-6">
          <h3 className="text-lg font-bold text-gold-800">{ar ? "حزمة المستثمر" : "Investor Package"}</h3>
          <p className="mt-2 text-sm text-gold-700">
            {ar
              ? "اجمع دراسة الجدوى والتحليل المالي والعرض التجاري وملف المنشأة في حزمة واحدة احترافية للمستثمرين."
              : "Combine your feasibility study, financial analysis, business proposal, and company profile into one professional investor package."}
          </p>
          <button className="mt-4 rounded-xl bg-gold-500 px-5 py-3 text-sm font-bold text-brand-900 shadow-card hover:bg-gold-400">
            {ar ? "إنشاء حزمة المستثمر" : "Create investor package"}
          </button>
        </section>
      </div>
    </div>
  );
}
