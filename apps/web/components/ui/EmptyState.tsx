"use client";

import Link from "next/link";

export type EmptyStateProps = {
  icon?: string;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
};

export function EmptyState({ icon, title, description, actionLabel, actionHref, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 px-6 py-16 text-center">
      {icon && <span className="mb-4 text-5xl opacity-60">{icon}</span>}
      <h3 className="text-lg font-bold text-ink-900">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-ink-600">{description}</p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="mt-6 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-card transition hover:bg-brand-700"
        >
          {actionLabel}
        </Link>
      )}
      {actionLabel && onAction && !actionHref && (
        <button
          onClick={onAction}
          className="mt-6 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-card transition hover:bg-brand-700"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
