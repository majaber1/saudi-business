"use client";

import { useLanguage } from "@/components/LanguageProvider";

export function Footer() {
  const { t } = useLanguage();
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="container-page flex flex-col gap-2 py-8 text-sm text-ink-700">
        <div className="font-semibold text-ink-900">{t.brand}</div>
        <p className="max-w-2xl text-slate-500">{t.footer.disclaimer}</p>
        <div className="text-slate-400">
          © {year} {t.brand} — {t.footer.rights}
        </div>
      </div>
    </footer>
  );
}
