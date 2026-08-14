"use client";

const variants = {
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  danger: "bg-red-50 text-red-700 border-red-200",
  info: "bg-blue-50 text-blue-700 border-blue-200",
  neutral: "bg-slate-100 text-ink-600 border-slate-200",
  brand: "bg-brand-50 text-brand-700 border-brand-200",
  gold: "bg-gold-50 text-gold-800 border-gold-200",
} as const;

export type BadgeProps = {
  variant?: keyof typeof variants;
  children: React.ReactNode;
};

export function Badge({ variant = "neutral", children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-bold ${variants[variant]}`}>
      {children}
    </span>
  );
}
