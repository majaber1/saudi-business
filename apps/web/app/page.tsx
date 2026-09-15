"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { getToken, listProjects, listV2Studies, type Project } from "@/lib/api";

interface StudySnapshot {
  study_id: number;
  project_id: number;
  phase: string;
  verdict?: string | null;
  language?: string;
  created_at?: string;
  updated_at?: string;
}

type ModuleStatus = "active" | "beta" | "coming";

interface ModuleCard {
  icon: string;
  nameAr: string;
  nameEn: string;
  descAr: string;
  descEn: string;
  status: ModuleStatus;
  href: string | null;
  testId: string;
}

const MODULES: ModuleCard[] = [
  {
    icon: "🔬",
    nameAr: "دراسة الجدوى بالذكاء الاصطناعي",
    nameEn: "AI Feasibility",
    descAr: "تحليل شامل لجدوى المشروع باستخدام الذكاء الاصطناعي",
    descEn: "Comprehensive AI-powered project feasibility analysis",
    status: "active",
    href: "/businesses",
    testId: "module-feasibility",
  },
  {
    icon: "🔍",
    nameAr: "ذكاء الأدلة",
    nameEn: "Evidence Intelligence",
    descAr: "تتبع الأدلة والمصادر وتقييم مستوى الثقة",
    descEn: "Track evidence, sources, and confidence levels",
    status: "active",
    href: "/businesses",
    testId: "module-evidence",
  },
  {
    icon: "📊",
    nameAr: "محاكي القرارات",
    nameEn: "Decision Simulator",
    descAr: "محاكاة سيناريوهات مالية متعددة للمقارنة",
    descEn: "Simulate multiple financial scenarios for comparison",
    status: "beta",
    href: null,
    testId: "module-simulator",
  },
  {
    icon: "💰",
    nameAr: "جاهزية التمويل",
    nameEn: "Funding Readiness",
    descAr: "تقييم جاهزية التمويل ومطابقة البرامج",
    descEn: "Assess funding readiness and match programs",
    status: "active",
    href: "/tools/funding",
    testId: "module-funding",
  },
  {
    icon: "🎯",
    nameAr: "رادار الفرص",
    nameEn: "Opportunity Radar",
    descAr: "اكتشف فرص استثمارية متوافقة مع ملفك",
    descEn: "Discover investment opportunities matching your profile",
    status: "active",
    href: "/tools/opportunities",
    testId: "module-opportunities",
  },
  {
    icon: "📡",
    nameAr: "المراقبة",
    nameEn: "Monitoring",
    descAr: "مراقبة مستمرة لمؤشرات الأداء والسوق",
    descEn: "Continuous monitoring of performance and market indicators",
    status: "coming",
    href: null,
    testId: "module-monitoring",
  },
  {
    icon: "📄",
    nameAr: "التقارير",
    nameEn: "Reports",
    descAr: "تقارير PDF و Word بالعربية والإنجليزية",
    descEn: "PDF & Word reports in Arabic and English",
    status: "active",
    href: "/tools/reports",
    testId: "module-reports",
  },
  {
    icon: "⚡",
    nameAr: "مركز الإجراءات",
    nameEn: "Action Center",
    descAr: "إدارة المهام والإجراءات المطلوبة",
    descEn: "Manage tasks and required actions",
    status: "coming",
    href: null,
    testId: "module-action-center",
  },
];

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

function verdictBadge(verdict: string | null | undefined, ar: boolean) {
  if (!verdict) return null;
  const styles: Record<string, string> = {
    GO: "bg-emerald-50 text-emerald-700 border-emerald-200",
    GO_WITH_CONDITIONS: "bg-amber-50 text-amber-700 border-amber-200",
    DEFER: "bg-orange-50 text-orange-700 border-orange-200",
    NO_GO: "bg-red-50 text-red-700 border-red-200",
  };
  const labels: Record<string, [string, string]> = {
    GO: ["انطلق", "GO"],
    GO_WITH_CONDITIONS: ["انطلق بشروط", "Conditional"],
    DEFER: ["تأجيل", "Defer"],
    NO_GO: ["لا تنطلق", "No Go"],
  };
  const style = styles[verdict] || "bg-slate-50 text-slate-600 border-slate-200";
  const label = labels[verdict];
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style}`}>
      {label ? label[ar ? 0 : 1] : verdict}
    </span>
  );
}

function deduplicateStudies(studies: StudySnapshot[]): StudySnapshot[] {
  const map = new Map<number, StudySnapshot>();
  for (const s of studies) {
    const existing = map.get(s.study_id);
    if (!existing || (s.updated_at && (!existing.updated_at || s.updated_at > existing.updated_at))) {
      map.set(s.study_id, s);
    }
  }
  return Array.from(map.values());
}

function ModuleStatusBadge({ status, ar }: { status: ModuleStatus; ar: boolean }) {
  if (status === "active") {
    return <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">{ar ? "نشط" : "ACTIVE"}</span>;
  }
  if (status === "beta") {
    return <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700">BETA</span>;
  }
  return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-ink-400">{ar ? "قريباً" : "COMING NEXT"}</span>;
}

export default function CommandCenterPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [projects, setProjects] = useState<Project[]>([]);
  const [studies, setStudies] = useState<StudySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    async function load() {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      setSignedIn(true);
      try {
        const [projs, studs] = await Promise.all([
          listProjects(token, true).catch(() => []),
          listV2Studies(token).catch(() => []),
        ]);
        setProjects(projs);
        setStudies(deduplicateStudies(studs as StudySnapshot[]));
      } catch {
        // graceful fallback
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const activeProjects = projects.filter((p) => !p.is_archived);
  const archivedCount = projects.filter((p) => p.is_archived).length;

  const studiesWithVerdict = studies.filter((s) => s.verdict);
  const studiesInProgress = studies.filter((s) => !s.verdict && s.phase !== "complete");

  const totalInvestment = activeProjects.reduce((sum, p) => sum + (Number(p.investment) || 0), 0);

  if (loading) {
    return (
      <div className="px-4 py-20 text-center lg:px-8">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
      </div>
    );
  }

  if (!signedIn) {
    return (
      <div className="px-4 py-16 lg:px-8">
        <div className="mx-auto max-w-lg text-center">
          <div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-brand-50 text-3xl text-brand-600">⌘</div>
          <h1 className="text-2xl font-bold text-ink-900">{ar ? "مركز التحكم" : "Command Center"}</h1>
          <p className="mt-2 text-sm text-ink-500">{ar ? "نظام تشغيل الأعمال بالذكاء الاصطناعي" : "AI Business Operating System"}</p>
          <p className="mt-3 text-sm text-ink-500">{ar ? "سجّل دخولك لعرض ملخص أعمالك" : "Sign in to view your business portfolio"}</p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/login" className="rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700">
              {ar ? "تسجيل الدخول" : "Sign in"}
            </Link>
            <Link href="/register" className="rounded-xl border border-slate-200 px-6 py-3 text-sm font-semibold text-ink-700 hover:border-brand-300">
              {ar ? "إنشاء حساب" : "Create account"}
            </Link>
          </div>

          {/* Module grid — discoverable even when signed out */}
          <div className="mt-12 text-start">
            <h2 className="mb-4 text-base font-bold text-ink-900">{ar ? "قدرات نظام التشغيل" : "Platform Capabilities"}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {MODULES.map((m) => (
                <div
                  key={m.testId}
                  data-testid={m.testId}
                  className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-start"
                >
                  <span className="mt-0.5 text-xl">{m.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-ink-900">{ar ? m.nameAr : m.nameEn}</span>
                      <ModuleStatusBadge status={m.status} ar={ar} />
                    </div>
                    <p className="mt-0.5 text-xs text-ink-500">{ar ? m.descAr : m.descEn}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 lg:px-8" data-testid="command-center">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-ink-900">{ar ? "مركز التحكم" : "Command Center"}</h1>
        <p className="mt-1 text-sm text-ink-500">{ar ? "نظام تشغيل الأعمال بالذكاء الاصطناعي" : "AI Business Operating System"}</p>
      </div>

      {/* KPI summary - real data only */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "الأعمال النشطة" : "Active Businesses"}</p>
          <p className="mt-2 text-2xl font-bold text-ink-900">{activeProjects.length}</p>
          {archivedCount > 0 && <p className="mt-1 text-xs text-ink-400">{archivedCount} {ar ? "مؤرشف" : "archived"}</p>}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "الدراسات الجارية" : "Studies in Progress"}</p>
          <p className="mt-2 text-2xl font-bold text-ink-900">{studiesInProgress.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "قرارات صادرة" : "Decisions Made"}</p>
          <p className="mt-2 text-2xl font-bold text-ink-900">{studiesWithVerdict.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium text-ink-500">{ar ? "إجمالي الاستثمار" : "Total Investment"}</p>
          <p className="mt-2 text-2xl font-bold text-ink-900">
            {totalInvestment > 0 ? money(totalInvestment, locale as "ar" | "en") : "—"}
          </p>
        </div>
      </div>

      {/* AI Business OS Module Grid */}
      <div className="mb-8">
        <h2 className="mb-4 text-lg font-bold text-ink-900">{ar ? "قدرات نظام التشغيل" : "Platform Capabilities"}</h2>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="module-grid">
          {MODULES.map((m) => {
            const disabled = m.status === "coming" || !m.href;
            const isBeta = m.status === "beta" && !m.href;

            if (disabled || isBeta) {
              return (
                <div
                  key={m.testId}
                  data-testid={m.testId}
                  className="flex flex-col rounded-2xl border border-slate-200 bg-white/60 p-5 opacity-70"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{m.icon}</span>
                    <ModuleStatusBadge status={m.status} ar={ar} />
                  </div>
                  <h3 className="mt-3 text-sm font-bold text-ink-700">{ar ? m.nameAr : m.nameEn}</h3>
                  <p className="mt-1 flex-1 text-xs text-ink-400">{ar ? m.descAr : m.descEn}</p>
                </div>
              );
            }

            return (
              <Link
                key={m.testId}
                href={m.href!}
                data-testid={m.testId}
                className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-card-hover"
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{m.icon}</span>
                  <ModuleStatusBadge status={m.status} ar={ar} />
                </div>
                <h3 className="mt-3 text-sm font-bold text-ink-900 group-hover:text-brand-700">{ar ? m.nameAr : m.nameEn}</h3>
                <p className="mt-1 flex-1 text-xs text-ink-500">{ar ? m.descAr : m.descEn}</p>
                <span className="mt-3 text-xs font-semibold text-brand-600 group-hover:text-brand-700">
                  {ar ? "فتح ←" : "Open →"}
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Active businesses or empty state */}
      {activeProjects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-2xl text-brand-600">◆</div>
          <h2 className="text-lg font-bold text-ink-900">{ar ? "لا توجد أعمال بعد" : "No businesses yet"}</h2>
          <p className="mt-2 text-sm text-ink-500">{ar ? "أنشئ عملك الأول لبدء رحلة التقييم" : "Create your first business to start the evaluation journey"}</p>
          <Link href="/businesses/new" className="mt-6 inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700">
            {ar ? "عمل جديد" : "New Business"}
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink-900">{ar ? "أعمالي" : "My Businesses"}</h2>
            <Link href="/businesses" className="text-sm font-semibold text-brand-600 hover:text-brand-700">
              {ar ? "عرض الكل" : "View all"} →
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {activeProjects.slice(0, 6).map((p) => {
              const projStudies = studies.filter((s) => s.project_id === p.id);
              const latestStudy = projStudies.length > 0 ? projStudies[projStudies.length - 1] : null;
              return (
                <Link
                  key={p.id}
                  href={`/businesses/${p.id}`}
                  data-testid={`business-card-${p.id}`}
                  className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-card-hover"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate text-base font-bold text-ink-900 group-hover:text-brand-700">{p.name}</h3>
                      <p className="mt-0.5 text-xs text-ink-500">{p.industry || (ar ? "غير محدد" : "Unspecified")}</p>
                    </div>
                    {latestStudy?.verdict && verdictBadge(latestStudy.verdict, ar)}
                  </div>
                  <div className="mt-4 flex items-center gap-4 text-xs text-ink-500">
                    <span>{projStudies.length} {ar ? "دراسة" : projStudies.length === 1 ? "study" : "studies"}</span>
                    {latestStudy && (
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-ink-600">
                        {phaseLabel(latestStudy.phase, ar)}
                      </span>
                    )}
                    {Number(p.investment) > 0 && (
                      <span>{money(Number(p.investment), locale as "ar" | "en")}</span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Studies needing attention */}
      {studiesInProgress.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-bold text-ink-900">{ar ? "دراسات تحتاج متابعة" : "Studies Needing Attention"}</h2>
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
            <div className="divide-y divide-slate-100">
              {studiesInProgress.slice(0, 5).map((s) => {
                const proj = projects.find((p) => p.id === s.project_id);
                return (
                  <Link
                    key={s.study_id}
                    href={`/businesses/${s.project_id}`}
                    className="flex items-center justify-between px-5 py-4 transition hover:bg-slate-50"
                  >
                    <div>
                      <p className="text-sm font-semibold text-ink-900">{proj?.name || `#${s.project_id}`}</p>
                      <p className="mt-0.5 text-xs text-ink-500">
                        {ar ? "المرحلة:" : "Phase:"} {phaseLabel(s.phase, ar)}
                      </p>
                    </div>
                    <span className="rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-700">
                      {ar ? "يحتاج متابعة" : "Action needed"}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          href="/businesses/new"
          data-testid="quick-new-business"
          className="flex items-center gap-3 rounded-2xl border border-dashed border-brand-300 bg-brand-50/50 p-4 text-sm font-semibold text-brand-700 transition hover:border-brand-400 hover:bg-brand-50"
        >
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-100 text-brand-600">+</span>
          {ar ? "إنشاء عمل جديد" : "Create New Business"}
        </Link>
        <Link
          href="/businesses"
          data-testid="quick-view-all"
          className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-ink-700 transition hover:border-brand-200 hover:text-brand-700"
        >
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-ink-500">◆</span>
          {ar ? "عرض كل الأعمال" : "View All Businesses"}
        </Link>
        <Link
          href="/tools/reports"
          className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-ink-700 transition hover:border-brand-200 hover:text-brand-700"
        >
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-ink-500">▤</span>
          {ar ? "التقارير" : "Reports"}
        </Link>
      </div>
    </div>
  );
}
