"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

/**
 * Bilingual (AR/EN) dashboard for Saudi Business | سعودي بزنس.
 *
 * Data note: summary/project/qualification figures below are clearly labeled
 * DEMO data. They render whenever the API base (NEXT_PUBLIC_API_BASE_URL) is
 * not configured for this environment (e.g. the Vercel Preview), so the page
 * is always a visible, working dashboard. When a live API is wired in, these
 * blocks can be swapped for fetched data.
 */

type Locale = "ar" | "en";

const copy: Record<Locale, any> = {
  ar: {
    demoBadge: "بيانات تجريبية",
    header: {
      title: "لوحة التحكم",
      subtitle: "نظرة شاملة على مشاريعك ودراسات الجدوى وفرص التمويل.",
      welcome: "مرحبًا بعودتك",
    },
    summary: {
      title: "الملخص",
      cards: [
        { key: "projects", label: "المشاريع", value: "4", hint: "مشروعان نشطان" },
        { key: "studies", label: "دراسات الجدوى", value: "3", hint: "دراسة واحدة قيد الإنجاز" },
        { key: "funding", label: "فرص التمويل المطابقة", value: "7", hint: "بقيمة تقديرية 2.4M ر.س" },
        { key: "reports", label: "التقارير", value: "5", hint: "جاهزة للتصدير" },
      ],
    },
    quick: {
      title: "إجراءات سريعة",
      actions: [
        { key: "project", label: "مشروع جديد", href: "/register" },
        { key: "study", label: "دراسة جدوى", href: "/register" },
        { key: "funding", label: "التمويل", href: "/funding" },
        { key: "report", label: "تقرير", href: "/register" },
      ],
    },
    projects: {
      title: "أحدث المشاريع",
      viewAll: "عرض الكل",
      empty: "لا توجد مشاريع بعد — ابدأ مشروعك الأول.",
      status: { active: "نشط", draft: "مسودة", review: "قيد المراجعة" },
      rows: [
        { name: "مقهى تخصصي — الرياض", industry: "الأغذية والمشروبات", investment: "850,000 ر.س", stage: "active" },
        { name: "منصّة توصيل طبي", industry: "الصحة", investment: "3,200,000 ر.س", stage: "review" },
        { name: "مركز لياقة ذكي", industry: "الرياضة", investment: "1,100,000 ر.س", stage: "draft" },
        { name: "مصنع تغليف مستدام", industry: "الصناعة", investment: "6,500,000 ر.س", stage: "active" },
      ],
      col: { name: "المشروع", industry: "القطاع", investment: "الاستثمار", stage: "الحالة" },
    },
    qualification: {
      title: "درجة التأهّل",
      subtitle: "مدى جاهزية مشروعك للتمويل والتراخيص.",
      score: 72,
      level: "جيد جدًا",
      breakdown: [
        { label: "اكتمال البيانات", value: 85 },
        { label: "المؤشرات المالية", value: 68 },
        { label: "الامتثال التنظيمي", value: 63 },
      ],
      cta: "تحسين الدرجة",
    },
    modules: {
      title: "الوحدات",
      items: [
        { key: "ideas", label: "بنك الأفكار", desc: "أفكار استثمارية متوافقة مع رؤية 2030.", href: "/ideas" },
        { key: "franchise", label: "الامتياز التجاري", desc: "فرص امتياز محلية وعالمية.", href: "/franchises" },
        { key: "auctions", label: "المزادات", desc: "أصول ومشاريع معروضة للبيع.", href: "/auctions" },
        { key: "qualification", label: "التأهّل", desc: "قيّم جاهزية مشروعك.", href: "/multazim" },
      ],
    },
  },
  en: {
    demoBadge: "Demo data",
    header: {
      title: "Dashboard",
      subtitle: "A complete overview of your projects, feasibility studies, and funding opportunities.",
      welcome: "Welcome back",
    },
    summary: {
      title: "Summary",
      cards: [
        { key: "projects", label: "Projects", value: "4", hint: "2 active" },
        { key: "studies", label: "Feasibility studies", value: "3", hint: "1 in progress" },
        { key: "funding", label: "Matched funding", value: "7", hint: "~SAR 2.4M potential" },
        { key: "reports", label: "Reports", value: "5", hint: "Ready to export" },
      ],
    },
    quick: {
      title: "Quick actions",
      actions: [
        { key: "project", label: "New Project", href: "/register" },
        { key: "study", label: "Feasibility Study", href: "/register" },
        { key: "funding", label: "Funding", href: "/funding" },
        { key: "report", label: "Report", href: "/register" },
      ],
    },
    projects: {
      title: "Recent projects",
      viewAll: "View all",
      empty: "No projects yet — start your first one.",
      status: { active: "Active", draft: "Draft", review: "In review" },
      rows: [
        { name: "Specialty Coffee — Riyadh", industry: "Food & Beverage", investment: "SAR 850,000", stage: "active" },
        { name: "Medical Delivery Platform", industry: "Healthcare", investment: "SAR 3,200,000", stage: "review" },
        { name: "Smart Fitness Center", industry: "Sports", investment: "SAR 1,100,000", stage: "draft" },
        { name: "Sustainable Packaging Plant", industry: "Manufacturing", investment: "SAR 6,500,000", stage: "active" },
      ],
      col: { name: "Project", industry: "Sector", investment: "Investment", stage: "Status" },
    },
    qualification: {
      title: "Qualification score",
      subtitle: "How ready your project is for funding and licensing.",
      score: 72,
      level: "Very good",
      breakdown: [
        { label: "Data completeness", value: 85 },
        { label: "Financial indicators", value: 68 },
        { label: "Regulatory compliance", value: 63 },
      ],
      cta: "Improve score",
    },
    modules: {
      title: "Modules",
      items: [
        { key: "ideas", label: "Idea Bank", desc: "Vision 2030-aligned investment ideas.", href: "/ideas" },
        { key: "franchise", label: "Franchise", desc: "Local and global franchise opportunities.", href: "/franchises" },
        { key: "auctions", label: "Auctions", desc: "Assets and businesses for sale.", href: "/auctions" },
        { key: "qualification", label: "Qualification", desc: "Assess your project readiness.", href: "/multazim" },
      ],
    },
  },
};

function StatusBadge({ stage, labels }: { stage: string; labels: Record<string, string> }) {
  const styles: Record<string, string> = {
    active: "bg-brand-100 text-brand-700",
    review: "bg-gold-100 text-gold-800",
    draft: "bg-slate-100 text-slate-600",
  };
  return (
    <span className={"inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium " + (styles[stage] ?? styles.draft)}>
      {labels[stage] ?? stage}
    </span>
  );
}

function Donut({ score }: { score: number }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - score / 100);
  return (
    <div className="relative h-36 w-36 shrink-0">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="url(#g)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0f8a4d" />
            <stop offset="100%" stopColor="#c9a227" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-ink-900">{score}</span>
        <span className="text-xs text-ink-700">/ 100</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { locale } = useLanguage();
  const c = copy[locale as Locale] ?? copy.en;

  return (
    <div className="bg-slate-50">
      {/* Header band */}
      <section className="relative overflow-hidden border-b border-brand-700 bg-gradient-to-br from-brand-700 via-brand-600 to-brand-900 text-white">
        <div className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(circle_at_top_right,theme(colors.gold.400),transparent_45%)]" />
        <div className="container-page relative py-12">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="text-sm font-medium text-gold-300">{c.header.welcome}</p>
              <h1 className="mt-1 text-3xl font-bold sm:text-4xl">{c.header.title}</h1>
              <p className="mt-3 max-w-xl text-sm text-white/80">{c.header.subtitle}</p>
            </div>
            <span className="rounded-full border border-gold-300/50 bg-white/10 px-3 py-1 text-xs font-medium text-gold-200 backdrop-blur">
              {c.demoBadge}
            </span>
          </div>
        </div>
      </section>

      <div className="container-page space-y-10 py-10">
        {/* Summary cards */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-ink-900">{c.summary.title}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {c.summary.cards.map((card: any) => (
              <div
                key={card.key}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-ink-700">{card.label}</p>
                  <span className="h-2 w-2 rounded-full bg-gradient-to-br from-brand-500 to-gold-500" />
                </div>
                <p className="mt-3 text-3xl font-bold text-ink-900">{card.value}</p>
                <p className="mt-1 text-xs text-ink-700">{card.hint}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Quick actions */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-ink-900">{c.quick.title}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {c.quick.actions.map((a: any) => (
              <Link
                key={a.key}
                href={a.href}
                className="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-brand-500 hover:shadow-md"
              >
                <span className="font-medium text-ink-800 group-hover:text-brand-700">{a.label}</span>
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-gold-500 text-lg font-bold text-white">
                  +
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Recent projects + qualification */}
        <section className="grid gap-6 lg:grid-cols-3">
          {/* Recent projects table */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <h2 className="text-lg font-semibold text-ink-900">{c.projects.title}</h2>
              <Link href="/register" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                {c.projects.viewAll}
              </Link>
            </div>
            {c.projects.rows.length === 0 ? (
              <p className="px-5 py-10 text-center text-sm text-ink-700">{c.projects.empty}</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-start text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-ink-700">
                      <th className="px-5 py-3 text-start font-medium">{c.projects.col.name}</th>
                      <th className="px-5 py-3 text-start font-medium">{c.projects.col.industry}</th>
                      <th className="px-5 py-3 text-start font-medium">{c.projects.col.investment}</th>
                      <th className="px-5 py-3 text-start font-medium">{c.projects.col.stage}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {c.projects.rows.map((p: any, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-5 py-3 font-medium text-ink-900">{p.name}</td>
                        <td className="px-5 py-3 text-ink-700">{p.industry}</td>
                        <td className="px-5 py-3 text-ink-700">{p.investment}</td>
                        <td className="px-5 py-3">
                          <StatusBadge stage={p.stage} labels={c.projects.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Qualification score */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-ink-900">{c.qualification.title}</h2>
            <p className="mt-1 text-sm text-ink-700">{c.qualification.subtitle}</p>
            <div className="mt-4 flex items-center gap-5">
              <Donut score={c.qualification.score} />
              <div>
                <span className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-sm font-semibold text-brand-700">
                  {c.qualification.level}
                </span>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              {c.qualification.breakdown.map((b: any) => (
                <div key={b.label}>
                  <div className="flex justify-between text-xs text-ink-700">
                    <span>{b.label}</span>
                    <span>{b.value}%</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-brand-500 to-gold-500"
                      style={{ width: b.value + "%" }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <Link
              href="/multazim"
              className="mt-5 inline-flex w-full items-center justify-center rounded-xl border border-brand-500 px-4 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
            >
              {c.qualification.cta}
            </Link>
          </div>
        </section>

        {/* Modules grid */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-ink-900">{c.modules.title}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {c.modules.items.map((m: any) => (
              <Link
                key={m.key}
                href={m.href}
                className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-brand-500 hover:shadow-md"
              >
                <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-600 to-gold-500" />
                <h3 className="mt-1 font-semibold text-brand-700">{m.label}</h3>
                <p className="mt-2 text-sm text-ink-700">{m.desc}</p>
                <span className="mt-4 inline-block text-sm font-medium text-gold-700 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5">
                  →
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
