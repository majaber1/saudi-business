"use client";

import Link from "next/link";

export type ServiceHeaderProps = {
  icon: string;
  title: string;
  subtitle: string;
  breadcrumb?: { label: string; href: string }[];
  actions?: React.ReactNode;
};

export function ServiceHeader({ icon, title, subtitle, breadcrumb, actions }: ServiceHeaderProps) {
  return (
    <section className="border-b border-slate-200 bg-white">
      <div className="container-page py-8">
        {breadcrumb && breadcrumb.length > 0 && (
          <nav className="mb-4 flex items-center gap-2 text-sm text-ink-500" aria-label="Breadcrumb">
            {breadcrumb.map((item, i) => (
              <span key={item.href} className="flex items-center gap-2">
                {i > 0 && <span className="text-ink-400">/</span>}
                <Link href={item.href} className="hover:text-brand-600">{item.label}</Link>
              </span>
            ))}
            <span className="text-ink-400">/</span>
            <span className="font-medium text-ink-800">{title}</span>
          </nav>
        )}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-brand-50 text-3xl">
              {icon}
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-ink-900 sm:text-3xl">{title}</h1>
              <p className="mt-1 text-sm text-ink-600">{subtitle}</p>
            </div>
          </div>
          {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
        </div>
      </div>
    </section>
  );
}
