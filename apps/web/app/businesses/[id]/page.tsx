"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { getToken, getProject, listStudies, listV2Studies, type Project, type Study } from "@/lib/api";

interface V2Study {
  study_id: number;
  project_id: number;
  phase: string;
  verdict?: string | null;
  decision_rationale?: string | null;
  language?: string;
  created_at?: string;
  updated_at?: string;
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

function verdictBadge(verdict: string, ar: boolean) {
  const styles: Record<string, string> = {
    GO: "bg-emerald-50 text-emerald-700 border-emerald-200",
    GO_WITH_CONDITIONS: "bg-amber-50 text-amber-700 border-amber-200",
    DEFER: "bg-orange-50 text-orange-700 border-orange-200",
    NO_GO: "bg-red-50 text-red-700 border-red-200",
    feasible: "bg-emerald-50 text-emerald-700 border-emerald-200",
    not_feasible: "bg-red-50 text-red-700 border-red-200",
    borderline: "bg-amber-50 text-amber-700 border-amber-200",
  };
  const labels: Record<string, [string, string]> = {
    GO: ["انطلق", "GO"],
    GO_WITH_CONDITIONS: ["انطلق بشروط", "Conditional"],
    DEFER: ["تأجيل", "Defer"],
    NO_GO: ["لا تنطلق", "No Go"],
    feasible: ["مجدٍ", "Feasible"],
    not_feasible: ["غير مجدٍ", "Not Feasible"],
    borderline: ["حدّي", "Borderline"],
  };
  const style = styles[verdict] || "bg-slate-50 text-slate-600 border-slate-200";
  const label = labels[verdict];
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${style}`}>
      {label ? label[ar ? 0 : 1] : verdict}
    </span>
  );
}

function stageBadge(stage: string | undefined, ar: boolean) {
  if (!stage) return null;
  const colors: Record<string, string> = {
    idea: "bg-blue-50 text-blue-700",
    mvp: "bg-purple-50 text-purple-700",
    active: "bg-emerald-50 text-emerald-700",
    review: "bg-amber-50 text-amber-700",
    draft: "bg-slate-100 text-slate-600",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors[stage] || "bg-slate-100 text-slate-600"}`}>
      {stage}
    </span>
  );
}

export default function BusinessHomePage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const params = useParams();
  const id = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [v1Studies, setV1Studies] = useState<Study[]>([]);
  const [v2Studies, setV2Studies] = useState<V2Study[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const token = getToken();
      if (!token) { setLoading(false); return; }

      try {
        const [p, s1, s2raw] = await Promise.all([
          getProject(token, Number(id)),
          listStudies(token, Number(id)).catch(() => []),
          listV2Studies(token).catch(() => []),
        ]);
        setProject(p);
        setV1Studies(s1);
        setV2Studies((s2raw as V2Study[]).filter((s) => s.project_id === Number(id)));
      } catch {
        // graceful
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [id]);

  if (loading) {
    return (
      <div className="px-4 py-20 text-center lg:px-8">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="px-4 py-20 text-center lg:px-8">
        <p className="text-lg text-ink-600">{ar ? "العمل غير موجود" : "Business not found"}</p>
        <Link href="/businesses" className="mt-4 inline-flex text-sm font-bold text-brand-600">{ar ? "العودة لأعمالي" : "Back to My Businesses"}</Link>
      </div>
    );
  }

  const latestV2 = v2Studies.length > 0 ? v2Studies[v2Studies.length - 1] : null;
  const latestVerdict = latestV2?.verdict || (v1Studies.find((s) => s.result?.verdict)?.result?.verdict);

  return (
    <div className="px-4 py-6 lg:px-8" data-testid="business-home">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-ink-500" aria-label="Breadcrumb">
        <Link href="/businesses" className="hover:text-brand-600">{ar ? "أعمالي" : "My Businesses"}</Link>
        <span className="mx-2">/</span>
        <span className="font-medium text-ink-800">{project.name}</span>
      </nav>

      {/* Business identity */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-ink-900">{project.name}</h1>
            {stageBadge(project.stage, ar)}
            {project.is_archived && (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-500">
                {ar ? "مؤرشف" : "Archived"}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-ink-500">{project.industry || (ar ? "قطاع غير محدد" : "Sector not specified")}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/projects/${id}`}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-ink-700 hover:border-brand-300 hover:text-brand-700"
          >
            {ar ? "مساحة العمل" : "Workspace"}
          </Link>
          <Link
            href={`/businesses/${id}/new-evaluation`}
            data-testid="start-new-evaluation"
            className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
          >
            {ar ? "تقييم جديد" : "New Evaluation"}
          </Link>
        </div>
      </div>

      {/* Summary cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "الاستثمار" : "Investment"}</p>
          <p className="mt-2 text-xl font-bold text-ink-900">
            {Number(project.investment) > 0 ? money(Number(project.investment), locale as "ar" | "en") : "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "عدد الدراسات" : "Studies"}</p>
          <p className="mt-2 text-xl font-bold text-ink-900">{v1Studies.length + v2Studies.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "المرحلة الحالية" : "Current Phase"}</p>
          <p className="mt-2 text-xl font-bold text-ink-900">
            {latestV2 ? phaseLabel(latestV2.phase, ar) : "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "آخر قرار" : "Latest Decision"}</p>
          <p className="mt-2">{latestVerdict ? verdictBadge(latestVerdict, ar) : <span className="text-xl font-bold text-ink-900">—</span>}</p>
        </div>
      </div>

      {/* Studies list */}
      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink-900">{ar ? "الدراسات" : "Evaluations"}</h2>
        </div>

        {v1Studies.length === 0 && v2Studies.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-sm text-ink-500">{ar ? "لا توجد دراسات بعد لهذا العمل" : "No evaluations yet for this business"}</p>
            <Link
              href={`/projects/${id}`}
              className="mt-4 inline-flex rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
            >
              {ar ? "ابدأ أول تقييم" : "Start First Evaluation"}
            </Link>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
            <div className="divide-y divide-slate-100">
              {/* V2 studies */}
              {v2Studies.map((s) => (
                <Link
                  key={`v2-${s.study_id}`}
                  href={`/projects/${id}/studies/${s.study_id}`}
                  data-testid={`study-row-${s.study_id}`}
                  className="flex items-center justify-between px-5 py-4 transition hover:bg-slate-50"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-ink-900">{ar ? `تقييم #${s.study_id}` : `Evaluation #${s.study_id}`}</p>
                      <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-600">v2</span>
                    </div>
                    <p className="mt-0.5 text-xs text-ink-500">
                      {ar ? "المرحلة:" : "Phase:"} {phaseLabel(s.phase, ar)}
                      {s.created_at && ` — ${new Date(s.created_at).toLocaleDateString(ar ? "ar-SA" : "en-SA")}`}
                    </p>
                  </div>
                  {s.verdict && verdictBadge(s.verdict, ar)}
                </Link>
              ))}
              {/* V1 studies */}
              {v1Studies.map((s) => (
                <Link
                  key={`v1-${s.id}`}
                  href={`/projects/${id}/studies/${s.id}`}
                  data-testid={`study-row-v1-${s.id}`}
                  className="flex items-center justify-between px-5 py-4 transition hover:bg-slate-50"
                >
                  <div>
                    <p className="font-semibold text-ink-900">{s.title}</p>
                    <p className="mt-0.5 text-xs text-ink-500">{s.study_type} — {s.status}</p>
                  </div>
                  {s.result?.verdict && verdictBadge(s.result.verdict, ar)}
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Recommended actions */}
      <section>
        <h2 className="mb-4 text-lg font-bold text-ink-900">{ar ? "الإجراءات المقترحة" : "Recommended Actions"}</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {v1Studies.length === 0 && v2Studies.length === 0 && (
            <Link
              href={`/projects/${id}`}
              className="flex items-center gap-3 rounded-2xl border border-dashed border-brand-300 bg-brand-50/50 p-4 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-100 text-brand-600">+</span>
              {ar ? "ابدأ أول دراسة جدوى" : "Start First Feasibility Study"}
            </Link>
          )}
          {latestV2 && !latestV2.verdict && (
            <Link
              href={`/projects/${id}/studies/${latestV2.study_id}`}
              className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50/50 p-4 text-sm font-semibold text-amber-800 hover:bg-amber-50"
            >
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-amber-100 text-amber-600">→</span>
              {ar ? `أكمل المرحلة: ${phaseLabel(latestV2.phase, ar)}` : `Continue: ${phaseLabel(latestV2.phase, ar)}`}
            </Link>
          )}
          <Link
            href={`/tools/financial?business=${id}`}
            className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-ink-700 hover:border-brand-200 hover:text-brand-700"
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-ink-500">↗</span>
            {ar ? "التحليل المالي" : "Financial Analysis"}
          </Link>
          <Link
            href={`/tools/reports?business=${id}`}
            className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-ink-700 hover:border-brand-200 hover:text-brand-700"
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-ink-500">▤</span>
            {ar ? "التقارير" : "Reports"}
          </Link>
        </div>
      </section>
    </div>
  );
}
