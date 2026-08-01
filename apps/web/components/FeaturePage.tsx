"use client";

import type { ReactNode } from "react";
import { useLanguage } from "@/components/LanguageProvider";

export type Bi = { ar: string; en: string };

export type FeaturePageProps = {
  title: Bi;
  intro: Bi;
  status: Bi;
  bullets?: Bi[];
  disclaimer?: Bi;
  children?: ReactNode;
};

export function FeaturePage({
  title,
  intro,
  status,
  bullets,
  disclaimer,
  children,
}: FeaturePageProps) {
  const { locale } = useLanguage();
  const pick = (b: Bi) => (locale === "ar" ? b.ar : b.en);
  const statusLabel = locale === "ar" ? "قيد التطوير" : "In progress";

  return (
    <main className="container-page py-14">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-semibold text-ink-900">{pick(title)}</h1>
        <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
          {statusLabel}
        </span>
      </div>

      <p className="mt-3 max-w-3xl text-ink-700">{pick(intro)}</p>
      <p className="mt-2 max-w-3xl text-sm text-ink-500">{pick(status)}</p>

      {bullets && bullets.length > 0 && (
        <ul className="mt-8 grid gap-3 sm:grid-cols-2">
          {bullets.map((b, i) => (
            <li
              key={i}
              className="rounded-xl border border-slate-200 bg-white p-5 text-ink-800 shadow-sm"
            >
              {pick(b)}
            </li>
          ))}
        </ul>
      )}

      {children}

      {disclaimer && (
        <p className="mt-8 max-w-3xl text-xs text-ink-500">{pick(disclaimer)}</p>
      )}
    </main>
  );
}
