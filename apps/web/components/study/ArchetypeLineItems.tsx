"use client";

type Lineage = { key?: string; value?: unknown; verification?: string };
type ArchetypeLine = {
  id?: string;
  monthly?: number | null;
  annual?: number | null;
  status?: string;
  lineage?: Lineage[];
};

const LABELS: Record<string, [string, string]> = {
  revenue: ["الإيراد", "Revenue"],
  rent: ["الإيجار", "Rent"],
  payroll: ["الرواتب", "Payroll"],
  operating_cost: ["تكلفة التشغيل", "Operating cost"],
  subscription_revenue: ["إيراد الاشتراك", "Subscription revenue"],
  acquisition_cost: ["تكلفة الاكتساب", "Acquisition cost"],
  hosting: ["الاستضافة", "Hosting"],
};

const STATUS: Record<string, [string, string]> = {
  MISSING: ["غير متوفر", "Missing"],
  ESTIMATED: ["تقديري", "Estimated"],
  AMBIGUOUS: ["الوحدة غير صريحة", "Unit not explicit"],
  OWNER_SUPPLIED: ["من المالك", "Owner supplied"],
};

function money(value: number | null | undefined, ar: boolean): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return ar ? "غير متوفر" : "Missing";
  }
  return new Intl.NumberFormat(ar ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function ArchetypeLineItems({
  ar,
  financial,
  onEdit,
  loading = false,
}: {
  ar: boolean;
  financial: Record<string, unknown> | null | undefined;
  onEdit?: (key: string, value: string) => Promise<void>;
  loading?: boolean;
}) {
  const lines = Array.isArray(financial?.lines) ? (financial!.lines as ArchetypeLine[]) : [];
  if (!lines.length) return null;
  const stale = financial?.stale === true;
  const basis = String(financial?.cash_flow_basis || "");
  const ceiling = financial?.verdict_override ? String(financial.verdict_override) : "";
  const monthlyNet = financial?.monthly_net;
  const annual = Array.isArray(financial?.annual_cash_flows)
    ? (financial!.annual_cash_flows as unknown[])
    : [];

  return (
    <div className="mt-3 space-y-2" data-testid="archetype-line-items">
      <p className="text-xs text-ink-600" data-testid="projection-basis">
        {ar
          ? "إسقاط تشغيلي قبل الضريبة. هذا ليس نموذجًا استثماريًا يشمل الضريبة."
          : "Pre-tax operating projection. This is not an investment-ready tax model."}
        {basis ? ` · ${basis}` : ""}
      </p>
      {stale ? (
        <p className="rounded-lg border border-amber-300 bg-amber-50 p-2 text-xs text-amber-950" data-testid="projection-stale">
          {ar
            ? "هذه الأرقام لا تطابق الافتراضات الحالية. أعد تشغيل التحليل قبل الاعتماد على التوصية."
            : "These figures do not match the current assumptions. Re-run the analysis before relying on a recommendation."}
        </p>
      ) : null}
      {ceiling ? (
        <p className="text-xs font-semibold text-ink-800" data-testid="recommendation-ceiling">
          {ar ? "سقف التوصية:" : "Recommendation ceiling:"} {ceiling}
        </p>
      ) : null}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-start text-ink-500">
              <th className="py-1 pe-2 font-medium">{ar ? "البند" : "Line"}</th>
              <th className="py-1 pe-2 font-medium">{ar ? "شهري" : "Monthly"}</th>
              <th className="py-1 pe-2 font-medium">{ar ? "سنوي" : "Annual"}</th>
              <th className="py-1 font-medium">{ar ? "المصدر" : "Source"}</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => {
              const id = String(line.id || "");
              const label = LABELS[id]?.[ar ? 0 : 1] || id;
              const status = STATUS[String(line.status || "")]?.[ar ? 0 : 1] || String(line.status || "");
              const sourceKey = line.lineage?.[0]?.key;
              return (
                <tr key={id} className="border-t border-slate-200" data-testid={`line-${id}`}>
                  <td className="py-1 pe-2 font-medium text-ink-900">{label}</td>
                  <td className="py-1 pe-2" data-testid={`line-${id}-monthly`}>{money(line.monthly, ar)}</td>
                  <td className="py-1 pe-2">{money(line.annual, ar)}</td>
                  <td className="py-1 text-ink-600">
                    <span>{status}</span>
                    {(line.lineage || []).map((item) => (
                      <span key={`${id}-${item.key}`} className="mt-0.5 block text-[11px]">
                        {item.key}: {String(item.value)} · {item.verification || ""}
                      </span>
                    ))}
                    {onEdit && sourceKey ? (
                      <form
                        className="mt-1 flex gap-1"
                        onSubmit={(event) => {
                          event.preventDefault();
                          const data = new FormData(event.currentTarget);
                          const value = String(data.get("value") || "").trim();
                          if (value) void onEdit(sourceKey, value);
                        }}
                      >
                        <input
                          name="value"
                          inputMode="decimal"
                          aria-label={ar ? `تعديل ${label}` : `Edit ${label}`}
                          data-testid={`edit-${id}`}
                          className="w-24 rounded border border-slate-300 px-1 py-0.5"
                        />
                        <button
                          type="submit"
                          disabled={loading}
                          className="rounded bg-slate-800 px-2 py-0.5 text-[11px] text-white disabled:opacity-50"
                        >
                          {ar ? "حفظ" : "Save"}
                        </button>
                      </form>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-ink-700" data-testid="monthly-net">
        {ar ? "صافي شهري:" : "Monthly net:"}{" "}
        {monthlyNet === null || monthlyNet === undefined ? (ar ? "غير متوفر" : "Missing") : money(Number(monthlyNet), ar)}
        {annual.length ? ` · ${ar ? "سنوي" : "Annual"} ${annual.map((value) => money(Number(value), ar)).join(" / ")}` : ""}
      </p>
    </div>
  );
}
