"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export function Footer() {
  const { t } = useLanguage();
  const year = new Date().getFullYear();

  const columns = [
    {
      title: t.footer.product,
      links: [
        { href: "/feasibility/new", label: t.footer.links.feasibility },
        { href: "/funding", label: t.footer.links.funding },
        { href: "/pricing", label: t.footer.links.pricing },
      ],
    },
    {
      title: t.footer.forInvestors,
      links: [{ href: "/opportunities", label: t.footer.links.opportunities }],
    },
    {
      title: t.footer.company,
      links: [
        { href: "/help", label: t.footer.links.help },
        { href: "https://github.com/majaber1/saudi-business", label: t.footer.links.source },
      ],
    },
  ];

  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="container-page grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 font-bold text-white">
              {t.brand[0]}
            </span>
            <span className="font-semibold text-ink-900">{t.brand}</span>
          </div>
          <p className="mt-4 max-w-xs text-sm text-ink-600">{t.tagline}</p>
        </div>

        {columns.map((col) => (
          <div key={col.title}>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-500">{col.title}</h3>
            <ul className="mt-4 space-y-2.5 text-sm text-ink-700">
              {col.links.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="hover:text-brand-600">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-slate-200">
        <div className="container-page flex flex-col gap-2 py-6 text-sm text-ink-600 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl text-ink-500">{t.footer.disclaimer}</p>
          <p className="whitespace-nowrap text-ink-500">
            © {year} {t.brand} — {t.footer.rights}
          </p>
        </div>
      </div>
    </footer>
  );
}
