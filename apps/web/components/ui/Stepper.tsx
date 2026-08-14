"use client";

export type StepperProps = {
  steps: string[];
  current: number;
};

export function Stepper({ steps, current }: StepperProps) {
  return (
    <nav className="flex items-center gap-2 overflow-x-auto pb-2" aria-label="Progress">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} className="flex items-center gap-2">
            {i > 0 && (
              <div className={`h-px w-6 shrink-0 ${done ? "bg-brand-500" : "bg-slate-200"}`} />
            )}
            <div className="flex shrink-0 items-center gap-2">
              <span
                className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold ${
                  done
                    ? "bg-brand-600 text-white"
                    : active
                      ? "border-2 border-brand-600 text-brand-700"
                      : "border border-slate-300 text-ink-500"
                }`}
              >
                {done ? "✓" : i + 1}
              </span>
              <span
                className={`whitespace-nowrap text-xs font-medium ${
                  active ? "text-brand-700" : done ? "text-ink-700" : "text-ink-500"
                }`}
              >
                {label}
              </span>
            </div>
          </div>
        );
      })}
    </nav>
  );
}
