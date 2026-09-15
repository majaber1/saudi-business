"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { Badge } from "@/components/ui/Badge";
import { getToken, listProjects, listV2Studies, type Project } from "@/lib/api";

interface StudySnapshot {
  study_id: number;
  project_id: number;
  phase: string;
  verdict?: string | null;
}

function money(value: number, locale: "ar" | "en") {
  return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

function phaseLabel(phase: string, ar: boolean): string {
  const map: Record<string, [string, string]> = {
    profile: ["الملف التعريفي", "Profile"],
    research: ["البحث", "Research"],
    evidence: ["الأدلة", "Evidence"],
    assumptions: ["الافتراضات", "Assumptions"],
    financial: ["التحليل المالي", "Financial"],
    decision: ["القرار", "Decision"],
    complete: ["مكتمل", "Complete"],
  };
  const m = map[phase];
  return m ? m[ar ? 0 : 1] : phase;
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
  const [studies, setStudies] = useState<StudySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    setSignedIn(true);
    Promise.all([
      listProjects(token, true).catch(() => []),
      listV2Studies(token).catch(() => []),
    ])
      .then(([p, s]) => {
        setProjects(p);
        setStudies(s as StudySnapshot[]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const active = projects.filter((p) => !p.is_archived);
  const archived = projects.filter((p) => p.is_archived);

  return (
    <div className="px-4 py-6 lg:px-8" data-testid="my-businesses">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">{ar ? "أعمالي" : "My Businesses"}</h1>
          <p className="mt-1 text-sm text-ink-500">{ar ? "أعمالك ودراساتها في مكان واحد" : "Your businesses and their evaluations in one place"}</p>
        </div>
        {signedIn && (
          <Link
            href="/businesses/new"
            data-testid="add-business-btn"
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-card hover:bg-brand-700"
          >
            {ar ? "عمل جديد" : "New Business"}
          </Link>
        )}
      </div>

      {!signedIn ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-card">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-2xl text-brand-600">◆</div>
          <h2 className="text-xl font-bold text-ink-900">{ar ? "سجّل دخولك لعرض أعمالك" : "Sign in to view your businesses"}</h2>
          <p className="mt-2 text-sm text-ink-500">{ar ? "أعمالك تربط جميع أدوات المنصة بسياق موحد" : "Your businesses connect all platform tools with unified context"}</p>
          <Link href="/login" className="mt-6 inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white">{ar ? "تسجيل الدخول" : "Sign in"}</Link>
        </div>
      ) : loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => <div key={i} className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}
        </div>
      ) : active.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-2xl text-brand-600">◆</div>
          <h2 className="text-lg font-bold text-ink-900">{ar ? "لا توجد أعمال بعد" : "No businesses yet"}</h2>
          <p className="mt-2 text-sm text-ink-500">{ar ? "أنشئ عملك الأول لبدء رحلة التقييم" : "Create your first business to start the evaluation journey"}</p>
          <Link href="/businesses/new" className="mt-6 inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700">
            {ar ? "عمل جديد" : "New Business"}
          </Link>
        </div>
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {active.map((p) => {
              const projStudies = studies.filter((s) => s.project_id === p.id);
              const latestStudy = projStudies.length > 0 ? projStudies[projStudies.length - 1] : null;
              const latestVerdict = latestStudy?.verdict;
              return (
                <Link key={p.id} href={`/businesses/${p.id}`} data-testid={`business-card-${p.id}`}>
                  <article className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-card-hover">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="truncate text-lg font-bold text-ink-900 group-hover:text-brand-700">{p.name}</h3>
                      {stageBadge(p.stage, ar)}
                    </div>
                    <p className="mt-1 text-sm text-ink-500">{p.industry || (ar ? "غير محدد" : "Unspecified")}</p>

                    <div className="mt-4 flex items-center gap-3 text-xs text-ink-500">
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium">
                        {projStudies.length} {ar ? "دراسة" : projStudies.length === 1 ? "study" : "studies"}
                      </span>
                      {latestStudy && (
                        <span className="rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-600">
                          {phaseLabel(latestStudy.phase, ar)}
                        </span>
                      )}
                      {latestVerdict && (
                        <span className={`rounded-full px-2 py-0.5 font-bold ${
                          latestVerdict === "GO" ? "bg-emerald-50 text-emerald-700" :
                          latestVerdict === "NO_GO" ? "bg-red-50 text-red-700" :
                          "bg-amber-50 text-amber-700"
                        }`}>
                          {latestVerdict}
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                      <span className="text-sm font-semibold text-ink-700">
                        {Number(p.investment) > 0 ? money(Number(p.investment), locale as "ar" | "en") : "—"}
                      </span>
                      <span className="text-xs text-ink-400">{new Date(p.created_at).toLocaleDateString(ar ? "ar-SA" : "en-SA")}</span>
                    </div>
                  </article>
                </Link>
              );
            })}
          </div>

          {archived.length > 0 && (
            <div className="mt-10">
              <h2 className="mb-4 text-lg font-bold text-ink-700">{ar ? "الأعمال المؤرشفة" : "Archived Businesses"}</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {archived.map((p) => (
                  <Link key={p.id} href={`/businesses/${p.id}`}>
                    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5 opacity-70 transition hover:opacity-100">
                      <h3 className="font-semibold text-ink-700">{p.name}</h3>
                      <p className="mt-1 text-sm text-ink-500">{p.industry} — {Number(p.investment) > 0 ? money(Number(p.investment), locale as "ar" | "en") : "—"}</p>
                    </article>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
