"use client";

export type KpiCardProps = {
  label: string;
  value: string;
  hint?: string;
  icon?: string;
};

export function KpiCard({ label, value, hint, icon }: KpiCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-ink-600">{label}</p>
        {icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-50 text-base">{icon}</span>
        )}
      </div>
      <p className="mt-4 truncate text-2xl font-bold tracking-tight text-ink-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-ink-500">{hint}</p>}
    </article>
  );
}
