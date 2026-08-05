"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export function Navbar() {
  const { t, locale, toggle } = useLanguage();

  const links = [
    { href: "/dashboard", label: locale === "ar" ? "لوحة التحكم" : "Dashboard" },
    { href: "/funding", label: t.nav.funding },
    { href: "/ideas", label: t.nav.ideas },
    { href: "/franchises", label: t.nav.franchises },
    { href: "/auctions", label: t.nav.auctions },
    { href: "/multazim", label: t.nav.multazim },
    { href: "/help", label: t.nav.help },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav className="container-page flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 font-bold text-white">
            {locale === "ar" ? "س" : "S"}
          </span>
          <span className="text-lg font-semibold text-ink-900">{t.brand}</span>
        </Link>

        <ul className="hidden items-center gap-6 text-sm text-ink-700 md:flex">
          {links.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="hover:text-brand-600">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <button
            onClick={toggle}
            aria-label="Switch language"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:border-brand-500 hover:text-brand-600"
          >
            {locale === "ar" ? "English" : "العربية"}
          </button>
          <Link
            href="/login"
            className="hidden rounded-md px-3 py-1.5 text-sm font-medium text-ink-700 hover:text-brand-600 sm:inline-block"
          >
            {t.nav.login}
          </Link>
          <Link
            href="/register"
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            {t.nav.register}
          </Link>
        </div>
      </nav>
    </header>
  );
}
