"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export default function HomePage() {
  const { t } = useLanguage();

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-b from-brand-50 to-white">
        <div className="container-page py-20">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-600">
            {t.tagline}
          </p>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight text-ink-900 sm:text-5xl">
            {t.hero.title}
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-ink-700">{t.hero.subtitle}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/register"
              className="rounded-lg bg-brand-600 px-6 py-3 font-medium text-white shadow-sm hover:bg-brand-700"
            >
              {t.hero.cta}
            </Link>
            <Link
              href="/funding"
              className="rounded-lg border border-slate-300 px-6 py-3 font-medium text-ink-800 hover:border-brand-500 hover:text-brand-600"
            >
              {t.hero.secondary}
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container-page py-16">
        <h2 className="text-2xl font-bold text-ink-900">{t.features.title}</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {t.features.items.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h3 className="text-lg font-semibold text-brand-700">{f.title}</h3>
              <p className="mt-2 text-sm text-ink-700">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Status strip */}
      <section className="border-t border-slate-200 bg-slate-50">
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
