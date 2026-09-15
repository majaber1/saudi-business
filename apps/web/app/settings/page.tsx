"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export default function SettingsPage() {
  const { locale, toggle } = useLanguage();
  const ar = locale === "ar";

  return (
    <div className="px-4 py-6 lg:px-8" data-testid="settings-page">
      <h1 className="mb-6 text-2xl font-bold text-ink-900">{ar ? "الإعدادات" : "Settings"}</h1>

      <div className="mx-auto max-w-2xl space-y-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink-900">{ar ? "اللغة" : "Language"}</h2>
          <p className="mt-1 text-sm text-ink-500">{ar ? "اختر لغة العرض المفضلة" : "Choose your preferred display language"}</p>
          <div className="mt-4 flex gap-3">
            <button
              onClick={() => { if (locale !== "ar") toggle(); }}
              className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${locale === "ar" ? "bg-brand-600 text-white" : "border border-slate-200 text-ink-700 hover:border-brand-300"}`}
            >
              العربية
            </button>
            <button
              onClick={() => { if (locale !== "en") toggle(); }}
              className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${locale === "en" ? "bg-brand-600 text-white" : "border border-slate-200 text-ink-700 hover:border-brand-300"}`}
            >
              English
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <h2 className="text-lg font-bold text-ink-900">{ar ? "الحساب" : "Account"}</h2>
          <p className="mt-1 text-sm text-ink-500">{ar ? "إدارة حسابك وتفضيلاتك" : "Manage your account and preferences"}</p>
          <div className="mt-4">
            <Link href="/account" className="text-sm font-semibold text-brand-600 hover:text-brand-700">
              {ar ? "إعدادات الحساب" : "Account settings"} →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
