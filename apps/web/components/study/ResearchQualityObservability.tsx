"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";

export type LocalizedText = { en?: string; ar?: string } | string | null | undefined;

export type EvidenceCard = {
  evidence_id: string;
  role?: string;
  role_label?: LocalizedText;
  source_key?: string | null;
  source_name?: LocalizedText;
  source_url?: string | null;
  authority_fit?: string | null;
  authority_label?: LocalizedText;
  freshness?: string | null;
  freshness_label?: LocalizedText;
  published_at?: string | null;
  retrieved_at?: string | null;
  geography?: string | null;
  period?: string | null;
  unit?: string | null;
  value?: unknown;
  statement?: string | null;
  quality_state?: string | null;
  quality_score?: number | null;
  document_id?: string | null;
  chunk_id?: string | null;
  provenance_kind?: string | null;
  provenance_label?: LocalizedText;
  selection_reason?: LocalizedText;
  official_validated?: boolean;
};

export type ObservabilityClaim = {
  claim_key: string;
  statement?: string | null;
  claim_type?: string | null;
  status: string;
  status_label?: LocalizedText;
  preferred_evidence?: EvidenceCard | null;
  alternate_evidence?: EvidenceCard[];
  conflict?: {
    status?: string;
    resolved?: boolean;
    unresolved?: boolean;
    explanation?: string;
    unresolved_message?: LocalizedText;
    candidates?: Array<{
      evidence_id: string;
      source_name?: LocalizedText;
      value?: unknown;
      period?: string | null;
      geography?: string | null;
      unit?: string | null;
      published_at?: string | null;
      authority_label?: LocalizedText;
      quality_state?: string | null;
      is_preferred?: boolean;
      role_label?: LocalizedText;
    }>;
  } | null;
  selection_reason?: LocalizedText;
};

export type ResearchQualityObservability = {
  observability_version?: string;
  policy_version?: string;
  claim_type?: string | null;
  summary?: {
    preferred_count?: number;
    alternate_count?: number;
    unresolved_conflict_count?: number;
    resolved_conflict_count?: number;
    stale_count?: number;
    unknown_freshness_count?: number;
    low_quality_count?: number;
    official_source_count?: number;
    total_evaluated?: number;
  };
  claims?: ObservabilityClaim[];
  preferred_evidence?: EvidenceCard[];
  alternate_evidence?: EvidenceCard[];
};

function localize(text: LocalizedText, ar: boolean): string {
  if (!text) return "";
  if (typeof text === "string") return text;
  return (ar ? text.ar || text.en : text.en || text.ar) || "";
}

function statusVariant(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  switch (status) {
    case "high_confidence":
      return "success";
    case "medium_confidence":
      return "info";
    case "conflict":
      return "warning";
    case "unresolved":
    case "low_confidence":
      return "danger";
    case "stale":
    case "freshness_unknown":
      return "warning";
    default:
      return "neutral";
  }
}

export function ClaimQualityBadge({
  status,
  label,
  ar,
  onClick,
}: {
  status: string;
  label?: LocalizedText;
  ar: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="claim-quality-badge"
      data-quality-status={status}
      className="inline-flex"
    >
      <Badge variant={statusVariant(status)}>{localize(label, ar) || status}</Badge>
    </button>
  );
}

function MetaRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-3 text-[11px]">
      <span className="text-ink-500">{label}</span>
      <span className="text-end font-medium text-ink-800">{value}</span>
    </div>
  );
}

function EvidenceDetails({ card, ar }: { card: EvidenceCard; ar: boolean }) {
  return (
    <div className="space-y-1.5 rounded-lg border border-slate-200 bg-slate-50 p-2" data-testid="evidence-card">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={card.role === "PREFERRED" ? "success" : "neutral"}>
          {localize(card.role_label, ar) || card.role || "—"}
        </Badge>
        {card.official_validated ? (
          <Badge variant="brand">{ar ? "رسمي موثّق" : "Validated official"}</Badge>
        ) : null}
        <span className="text-xs font-semibold text-ink-800">{localize(card.source_name, ar)}</span>
      </div>
      {card.statement ? <p className="text-xs text-ink-700">{card.statement}</p> : null}
      <MetaRow label={ar ? "السلطة" : "Authority"} value={localize(card.authority_label, ar)} />
      <MetaRow label={ar ? "الحداثة" : "Freshness"} value={localize(card.freshness_label, ar)} />
      <MetaRow
        label={ar ? "تاريخ النشر" : "Published"}
        value={card.published_at || (ar ? "غير متوفر" : "Unavailable")}
      />
      <MetaRow label={ar ? "تاريخ الاسترجاع" : "Retrieved"} value={card.retrieved_at || undefined} />
      <MetaRow label={ar ? "الفترة" : "Period"} value={card.period || undefined} />
      <MetaRow label={ar ? "الجغرافيا" : "Geography"} value={card.geography || undefined} />
      <MetaRow label={ar ? "الوحدة" : "Unit"} value={card.unit || undefined} />
      <MetaRow
        label={ar ? "القيمة" : "Value"}
        value={card.value === null || card.value === undefined ? undefined : String(card.value)}
      />
      <MetaRow label={ar ? "المصدر" : "Provenance"} value={localize(card.provenance_label, ar)} />
      {card.selection_reason ? (
        <p className="rounded bg-white p-2 text-[11px] text-ink-700" data-testid="selection-reason">
          <span className="font-semibold">{ar ? "لماذا هذا المصدر؟ " : "Why this source? "}</span>
          {localize(card.selection_reason, ar)}
        </p>
      ) : null}
      {card.source_url ? (
        <a
          href={card.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block break-all text-[11px] text-brand-700 hover:underline"
        >
          {card.source_url}
        </a>
      ) : null}
    </div>
  );
}

export function EvidenceDrawer({
  open,
  onClose,
  claim,
  ar,
}: {
  open: boolean;
  onClose: () => void;
  claim: ObservabilityClaim | null;
  ar: boolean;
}) {
  if (!open || !claim) return null;
  const preferred = claim.preferred_evidence;
  const alternates = claim.alternate_evidence || [];
  const conflict = claim.conflict;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-3 sm:items-center"
      data-testid="evidence-drawer"
    >
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-4 shadow-xl">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-ink-900">
              {ar ? "تفاصيل الدليل" : "Evidence details"}
            </p>
            <div className="mt-1">
              <ClaimQualityBadge status={claim.status} label={claim.status_label} ar={ar} />
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm text-ink-500 hover:bg-slate-100"
            data-testid="evidence-drawer-close"
          >
            {ar ? "إغلاق" : "Close"}
          </button>
        </div>

        {claim.statement ? <p className="mb-3 text-sm text-ink-800">{claim.statement}</p> : null}

        {conflict?.unresolved ? (
          <div
            className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
            data-testid="unresolved-conflict-banner"
          >
            <p className="font-bold">{ar ? "تعارض غير محسوم" : "Unresolved conflict"}</p>
            <p className="mt-1">
              {localize(conflict.unresolved_message, ar) ||
                (ar ? "يبقى التعارض غير محسوم." : "Conflicting evidence remains unresolved.")}
            </p>
          </div>
        ) : null}

        {conflict && (conflict.candidates || []).length > 0 ? (
          <div className="mb-3" data-testid="conflict-candidates">
            <p className="mb-1 text-xs font-semibold text-ink-700">
              {ar ? "المرشحون المتعارضون" : "Conflicting candidates"}
            </p>
            <ul className="space-y-2">
              {(conflict.candidates || []).map((candidate) => (
                <li
                  key={candidate.evidence_id}
                  className="rounded-lg border border-amber-100 bg-amber-50/60 p-2 text-[11px]"
                >
                  <p className="font-semibold">{localize(candidate.source_name, ar)}</p>
                  <p>
                    {candidate.value !== undefined && candidate.value !== null
                      ? String(candidate.value)
                      : "—"}
                    {candidate.unit ? ` ${candidate.unit}` : ""}
                    {candidate.period ? ` · ${candidate.period}` : ""}
                    {candidate.geography ? ` · ${candidate.geography}` : ""}
                  </p>
                  <p className="text-ink-500">
                    {localize(candidate.authority_label, ar)}
                    {candidate.is_preferred ? ` · ${ar ? "مفضل" : "Preferred"}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {preferred ? (
          <div className="mb-3">
            <p className="mb-1 text-xs font-semibold text-ink-700">
              {ar ? "الدليل المفضل" : "Preferred evidence"}
            </p>
            <EvidenceDetails card={preferred} ar={ar} />
          </div>
        ) : conflict?.unresolved ? null : (
          <p className="mb-3 text-xs text-ink-500">
            {ar ? "لا يوجد دليل مفضل" : "No preferred evidence"}
          </p>
        )}

        {alternates.length > 0 ? (
          <div>
            <p className="mb-1 text-xs font-semibold text-ink-700">
              {ar ? "أدلة بديلة" : "Alternate evidence"}
            </p>
            <div className="space-y-2">
              {alternates.map((card) => (
                <EvidenceDetails key={card.evidence_id} card={card} ar={ar} />
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ResearchQualitySummary({
  observability,
  ar,
}: {
  observability: ResearchQualityObservability | null | undefined;
  ar: boolean;
}) {
  const summary = observability?.summary;
  if (!summary) return null;
  const items = [
    { key: "preferred", label: ar ? "مفضل" : "Preferred", value: summary.preferred_count ?? 0 },
    {
      key: "unresolved",
      label: ar ? "غير محسوم" : "Unresolved",
      value: summary.unresolved_conflict_count ?? 0,
    },
    { key: "stale", label: ar ? "قديم" : "Stale", value: summary.stale_count ?? 0 },
    {
      key: "unknown",
      label: ar ? "حداثة مجهولة" : "Freshness unknown",
      value: summary.unknown_freshness_count ?? 0,
    },
    { key: "low", label: ar ? "جودة منخفضة" : "Low quality", value: summary.low_quality_count ?? 0 },
    {
      key: "official",
      label: ar ? "رسمي" : "Official",
      value: summary.official_source_count ?? 0,
    },
  ];
  return (
    <section
      className="rounded-xl border border-slate-200 bg-white p-3"
      data-testid="research-quality-summary"
    >
      <h2 className="text-sm font-semibold text-ink-900">
        {ar ? "صحة جودة البحث" : "Research quality health"}
      </h2>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.key}
            className="rounded-lg bg-slate-50 px-2 py-1.5"
            data-testid={`rq-metric-${item.key}`}
          >
            <p className="text-[10px] text-ink-500">{item.label}</p>
            <p className="text-sm font-bold text-ink-900">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function ResearchQualityClaimsList({
  observability,
  ar,
}: {
  observability: ResearchQualityObservability | null | undefined;
  ar: boolean;
}) {
  const [active, setActive] = useState<ObservabilityClaim | null>(null);
  const claims = useMemo(() => observability?.claims || [], [observability]);
  if (!claims.length) return null;

  return (
    <section
      className="rounded-xl border border-slate-200 bg-white p-3"
      data-testid="research-quality-claims"
    >
      <h2 className="text-sm font-semibold text-ink-900">
        {ar ? `جودة الادعاءات (${claims.length})` : `Claim quality (${claims.length})`}
      </h2>
      <ul className="mt-2 space-y-2">
        {claims.map((claim) => (
          <li
            key={claim.claim_key}
            className="rounded-lg bg-slate-50 p-2"
            data-testid="rq-claim-row"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs text-ink-800">{claim.statement || claim.claim_key}</p>
              <ClaimQualityBadge
                status={claim.status}
                label={claim.status_label}
                ar={ar}
                onClick={() => setActive(claim)}
              />
            </div>
            <button
              type="button"
              className="mt-1 text-[11px] font-semibold text-brand-700 hover:underline"
              data-testid="open-evidence-drawer"
              onClick={() => setActive(claim)}
            >
              {ar ? "عرض الأدلة" : "View evidence"}
            </button>
          </li>
        ))}
      </ul>
      <EvidenceDrawer open={!!active} onClose={() => setActive(null)} claim={active} ar={ar} />
    </section>
  );
}
