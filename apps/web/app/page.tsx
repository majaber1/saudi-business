"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export default function HomePage() {
  const { t } = useLanguage();

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-50 via-white to-white">
        <div className="pointer-events-none absolute inset-0 opacity-[0.07] [background:radial-gradient(circle_at_85%_15%,theme(colors.gold.500),transparent_45%)]" />
        <div className="container-page relative py-24">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-700">
            {t.tagline}
          </p>
          <h1 className="max-w-3xl text-4xl font-bold leading-[1.15] tracking-tight text-ink-900 sm:text-5xl">
            {t.hero.title}
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-ink-600">{t.hero.subtitle}</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link
              href="/feasibility/new"
              className="rounded-lg bg-brand-600 px-6 py-3 font-medium text-white shadow-card transition hover:bg-brand-700 hover:shadow-card-hover"
            >
              {t.hero.cta}
            </Link>
            <Link
              href="/funding"
              className="rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-ink-800 transition hover:border-brand-500 hover:text-brand-600"
            >
              {t.hero.secondary}
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container-page py-16">
        <h2 className="text-2xl font-bold tracking-tight text-ink-900">{t.features.title}</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {t.features.items.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover"
            >
              <h3 className="text-lg font-semibold text-brand-700">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-600">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Investors */}
      <section className="border-y border-brand-800 bg-gradient-to-br from-brand-800 via-brand-700 to-brand-900">
        <div className="container-page flex flex-col items-start justify-between gap-6 py-14 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-2xl font-bold text-white">{t.investors.title}</h2>
            <p className="mt-2 max-w-xl text-sm text-white/80">{t.investors.body}</p>
          </div>
          <Link
            href="/opportunities"
            className="shrink-0 rounded-lg bg-gold-500 px-6 py-3 font-medium text-brand-900 shadow-card transition hover:bg-gold-400"
          >
            {t.investors.cta}
          </Link>
        </div>
      </section>

      {/* Status strip */}
      <section className="border-b border-slate-200 bg-slate-50">
        <div className="container-page py-10">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
            <h3 className="font-semibold text-amber-800">{t.status.title}</h3>
            <p className="mt-1 text-sm text-amber-700">{t.status.body}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
