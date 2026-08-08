"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export function Navbar() {
  const { t, locale, toggle } = useLanguage();

  // Kept intentionally short for a clean, professional first impression --
  // Franchises/Auctions/Multazim stay reachable from the dashboard modules
  // grid and the footer rather than crowding the primary nav.
  const links = [
    { href: "/dashboard", label: locale === "ar" ? "لوحة التحكم" : "Dashboard" },
    { href: "/opportunities", label: t.nav.opportunities },
    { href: "/funding", label: t.nav.funding },
    { href: "/qualification", label: locale === "ar" ? "التأهيل" : "Qualification" },
    { href: "/ideas", label: t.nav.ideas },
    { href: "/pricing", label: t.nav.pricing },
    { href: "/help", label: t.nav.help },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/85 backdrop-blur-md">
      <nav className="container-page flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 font-bold text-white shadow-card">
            {locale === "ar" ? "س" : "S"}
          </span>
          <span className="text-lg font-semibold tracking-tight text-ink-900">{t.brand}</span>
        </Link>

        <ul className="hidden items-center gap-7 text-sm font-medium text-ink-600 md:flex">
          {links.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="transition-colors hover:text-brand-600">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <button
            onClick={toggle}
            aria-label="Switch language"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-ink-700 transition-colors hover:border-brand-500 hover:text-brand-600"
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
            className="rounded-md bg-brand-600 px-4 py-1.5 text-sm font-medium text-white shadow-card transition-colors hover:bg-brand-700"
          >
            {t.nav.register}
          </Link>
        </div>
      </nav>
    </header>
  );
}
