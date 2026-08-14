"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Stepper } from "@/components/ui/Stepper";
import { Badge } from "@/components/ui/Badge";
import { getToken, listProposals, createProposal, type Proposal } from "@/lib/api";

const proposalTypes = [
  { key: "commercial", icon: "🤝", ar: "عرض تجاري", en: "Commercial Proposal" },
  { key: "technical", icon: "⚙️", ar: "عرض فني", en: "Technical Proposal" },
  { key: "government", icon: "🏛️", ar: "عرض حكومي", en: "Government Proposal" },
  { key: "investor", icon: "💼", ar: "عرض للمستثمرين", en: "Investor Proposal" },
  { key: "consulting", icon: "📋", ar: "عرض استشاري", en: "Consulting Proposal" },
  { key: "partnership", icon: "🤝", ar: "عرض شراكة", en: "Partnership Proposal" },
];

const steps = {
  ar: ["نوع العرض", "العميل / المستلم", "النطاق والحل", "التسعير والجدول", "المراجعة والتصدير"],
  en: ["Proposal type", "Client / recipient", "Scope & solution", "Pricing & timeline", "Review & export"],
};

type ProposalDraft = {
  title: string;
  proposal_type: string;
  client_name: string;
  client_email: string;
  client_company: string;
  scope: string;
  deliverables: string;
  methodology: string;
  price: string;
  currency: string;
  timeline: string;
  validity_days: string;
  terms: string;
};

const emptyDraft: ProposalDraft = {
  title: "",
  proposal_type: "",
  client_name: "",
  client_email: "",
  client_company: "",
  scope: "",
  deliverables: "",
  methodology: "",
  price: "",
  currency: "SAR",
  timeline: "",
  validity_days: "30",
  terms: "",
};

export default function ProposalBuilderPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [mode, setMode] = useState<"list" | "new">("list");
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [draft, setDraft] = useState<ProposalDraft>(emptyDraft);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (token) listProposals(token).then(setProposals).catch(() => {});
  }, [mode]);

  const set = (field: keyof ProposalDraft, value: string) =>
    setDraft((prev) => ({ ...prev, [field]: value }));

  async function handleSave() {
    const token = getToken();
    if (!token) return;
    setSaving(true);
    try {
      await createProposal(token, {
        title: draft.title || `${selectedType} proposal`,
        proposal_type: selectedType || "commercial",
        locale: ar ? "ar" : "en",
        payload: {
          client_name: draft.client_name,
          client_email: draft.client_email,
          client_company: draft.client_company,
          scope: draft.scope,
          deliverables: draft.deliverables,
          methodology: draft.methodology,
          price: draft.price,
          currency: draft.currency,
          timeline: draft.timeline,
          validity_days: draft.validity_days,
          terms: draft.terms,
        },
      });
      setMode("list");
      setCurrentStep(0);
      setDraft(emptyDraft);
    } catch {
    } finally {
      setSaving(false);
    }
  }

  if (mode === "new") {
    return (
      <div className="min-h-screen bg-[#f5f7f6]">
        <ServiceHeader
          icon="📝"
          title={ar ? "عرض جديد" : "New Proposal"}
          subtitle={ar ? "أنشئ عرضًا احترافيًا خطوة بخطوة" : "Build a professional proposal step by step"}
          breadcrumb={[
            { label: ar ? "الأدوات" : "Tools", href: "/tools" },
            { label: ar ? "منشئ العروض" : "Proposal Builder", href: "/tools/proposal" },
          ]}
        />
        <div className="container-page space-y-8 py-8">
          <Stepper steps={ar ? steps.ar : steps.en} current={currentStep} />

          {currentStep === 0 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">{ar ? "اختر نوع العرض" : "Choose proposal type"}</h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {proposalTypes.map((pt) => (
                  <button
                    key={pt.key}
                    onClick={() => { setSelectedType(pt.key); setCurrentStep(1); }}
                    className={`group rounded-xl border p-5 text-start transition hover:-translate-y-0.5 hover:shadow-card-hover ${
                      selectedType === pt.key ? "border-brand-500 bg-brand-50" : "border-slate-200 bg-white hover:border-brand-300"
                    }`}
                  >
                    <span className="text-2xl">{pt.icon}</span>
                    <p className="mt-3 font-bold text-ink-900">{ar ? pt.ar : pt.en}</p>
                  </button>
                ))}
              </div>

              <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4">
                <p className="text-sm text-blue-800">
                  {ar
                    ? "💡 إذا كانت لديك دراسة جدوى موجودة، يمكنك استيراد البيانات تلقائيًا."
                    : "💡 If you have an existing feasibility study, you can import data automatically."}
                </p>
                <button className="mt-2 text-sm font-bold text-blue-700 hover:text-blue-800">
                  {ar ? "استيراد من دراسة الجدوى" : "Import from Feasibility Study"}
                </button>
              </div>
            </section>
          )}

          {currentStep === 1 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">{ar ? "العميل / المستلم" : "Client / Recipient"}</h2>
              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "عنوان العرض" : "Proposal title"}</label>
                  <input value={draft.title} onChange={(e) => set("title", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "عنوان العرض" : "Proposal title"} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "اسم العميل" : "Client name"}</label>
                  <input value={draft.client_name} onChange={(e) => set("client_name", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "بريد العميل" : "Client email"}</label>
                  <input type="email" value={draft.client_email} onChange={(e) => set("client_email", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "شركة العميل" : "Client company"}</label>
                  <input value={draft.client_company} onChange={(e) => set("client_company", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" />
                </div>
              </div>
              <StepNav ar={ar} step={currentStep} setStep={setCurrentStep} />
            </section>
          )}

          {currentStep === 2 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">{ar ? "النطاق والحل" : "Scope & Solution"}</h2>
              <div className="mt-6 space-y-5">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "نطاق العمل" : "Scope of work"}</label>
                  <textarea value={draft.scope} onChange={(e) => set("scope", e.target.value)} rows={4} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "وصف نطاق العمل المقترح..." : "Describe the proposed scope of work..."} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "المخرجات" : "Deliverables"}</label>
                  <textarea value={draft.deliverables} onChange={(e) => set("deliverables", e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "ما الذي سيتسلمه العميل..." : "What the client will receive..."} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "المنهجية" : "Methodology"}</label>
                  <textarea value={draft.methodology} onChange={(e) => set("methodology", e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "النهج المقترح لتنفيذ العمل..." : "Proposed approach to executing the work..."} />
                </div>
              </div>
              <StepNav ar={ar} step={currentStep} setStep={setCurrentStep} />
            </section>
          )}

          {currentStep === 3 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">{ar ? "التسعير والجدول الزمني" : "Pricing & Timeline"}</h2>
              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "السعر الإجمالي" : "Total price"}</label>
                  <input type="number" value={draft.price} onChange={(e) => set("price", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder="0" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "العملة" : "Currency"}</label>
                  <select value={draft.currency} onChange={(e) => set("currency", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none">
                    <option value="SAR">SAR</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "الجدول الزمني" : "Timeline"}</label>
                  <input value={draft.timeline} onChange={(e) => set("timeline", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "مثال: 4 أسابيع" : "e.g. 4 weeks"} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "صلاحية العرض (أيام)" : "Validity (days)"}</label>
                  <input type="number" value={draft.validity_days} onChange={(e) => set("validity_days", e.target.value)} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-ink-700">{ar ? "الشروط والأحكام" : "Terms & conditions"}</label>
                  <textarea value={draft.terms} onChange={(e) => set("terms", e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none" placeholder={ar ? "شروط الدفع، الضمانات..." : "Payment terms, warranties..."} />
                </div>
              </div>
              <StepNav ar={ar} step={currentStep} setStep={setCurrentStep} />
            </section>
          )}

          {currentStep === 4 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">{ar ? "المراجعة والتصدير" : "Review & Export"}</h2>
              <div className="mt-6 space-y-4">
                <ReviewRow label={ar ? "نوع العرض" : "Type"} value={proposalTypes.find((t) => t.key === selectedType)?.[ar ? "ar" : "en"] || selectedType || "—"} />
                <ReviewRow label={ar ? "العنوان" : "Title"} value={draft.title || "—"} />
                <ReviewRow label={ar ? "العميل" : "Client"} value={draft.client_name || "—"} />
                <ReviewRow label={ar ? "الشركة" : "Company"} value={draft.client_company || "—"} />
                <ReviewRow label={ar ? "النطاق" : "Scope"} value={draft.scope || "—"} />
                <ReviewRow label={ar ? "المخرجات" : "Deliverables"} value={draft.deliverables || "—"} />
                <ReviewRow label={ar ? "السعر" : "Price"} value={draft.price ? `${draft.price} ${draft.currency}` : "—"} />
                <ReviewRow label={ar ? "الجدول الزمني" : "Timeline"} value={draft.timeline || "—"} />
                <ReviewRow label={ar ? "الصلاحية" : "Validity"} value={`${draft.validity_days} ${ar ? "يوم" : "days"}`} />
              </div>
              <div className="mt-6 flex justify-between">
                <button onClick={() => setCurrentStep(3)} className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-ink-700 hover:border-brand-500">{ar ? "السابق" : "Previous"}</button>
                <button onClick={handleSave} disabled={saving} className="rounded-xl bg-gold-500 px-5 py-3 text-sm font-bold text-brand-900 hover:bg-gold-400 disabled:opacity-50">
                  {saving ? (ar ? "جاري الحفظ..." : "Saving...") : (ar ? "حفظ العرض" : "Save proposal")}
                </button>
              </div>
            </section>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f7f6]">
      <ServiceHeader
        icon="📝"
        title={ar ? "منشئ العروض" : "Proposal Builder"}
        subtitle={ar
          ? "أنشئ عروضًا تجارية احترافية باللغتين العربية والإنجليزية"
          : "Build professional business proposals in Arabic and English"}
        breadcrumb={[{ label: ar ? "الأدوات" : "Tools", href: "/tools" }]}
        actions={
          <button
            onClick={() => setMode("new")}
            className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-card hover:bg-brand-700"
          >
            {ar ? "عرض جديد" : "New proposal"}
          </button>
        }
      />

      <div className="container-page space-y-8 py-8">
        <section className="rounded-2xl border border-brand-200 bg-white p-6 shadow-card sm:p-8">
          <h2 className="text-xl font-bold text-ink-900">{ar ? "أنواع العروض" : "Proposal types"}</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {proposalTypes.map((pt) => (
              <button
                key={pt.key}
                onClick={() => { setSelectedType(pt.key); setMode("new"); setCurrentStep(0); }}
                className="group rounded-xl border border-slate-200 bg-white p-5 text-start transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card-hover"
              >
                <span className="text-2xl">{pt.icon}</span>
                <p className="mt-3 font-bold text-ink-900 group-hover:text-brand-700">{ar ? pt.ar : pt.en}</p>
              </button>
            ))}
          </div>
        </section>

        {proposals.length > 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-white shadow-card">
            <header className="border-b border-slate-100 px-5 py-4">
              <h2 className="font-bold text-ink-900">{ar ? "العروض السابقة" : "Your proposals"}</h2>
            </header>
            <div className="divide-y divide-slate-100">
              {proposals.map((p) => (
                <div key={p.id} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50">
                  <div>
                    <p className="font-semibold text-ink-900">{p.title}</p>
                    <p className="mt-1 text-xs text-ink-500">{proposalTypes.find((t) => t.key === p.proposal_type)?.[ar ? "ar" : "en"] || p.proposal_type}</p>
                  </div>
                  <Badge variant={p.status === "completed" ? "success" : p.status === "draft" ? "neutral" : "info"}>{p.status}</Badge>
                </div>
              ))}
            </div>
          </section>
        ) : (
          <EmptyState
            icon="📝"
            title={ar ? "لا توجد عروض سابقة" : "No previous proposals"}
            description={ar ? "ابدأ بإنشاء عرضك التجاري الأول." : "Start by creating your first business proposal."}
            actionLabel={ar ? "عرض جديد" : "New proposal"}
            onAction={() => setMode("new")}
          />
        )}

        <section className="rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h3 className="font-semibold text-blue-800">{ar ? "ربط اختياري" : "Optional linking"}</h3>
          <p className="mt-2 text-sm text-blue-700">
            {ar
              ? "يمكنك ربط العرض بمشروع موجود لاستيراد البيانات تلقائيًا، أو إنشاء عرض مستقل بالكامل."
              : "You can link your proposal to an existing business to auto-import data, or create a fully independent proposal."}
          </p>
        </section>
      </div>
    </div>
  );
}

function StepNav({ ar, step, setStep }: { ar: boolean; step: number; setStep: (s: number) => void }) {
  return (
    <div className="mt-6 flex justify-between">
      <button onClick={() => setStep(Math.max(0, step - 1))} className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-ink-700 hover:border-brand-500">{ar ? "السابق" : "Previous"}</button>
      <button onClick={() => setStep(step + 1)} className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700">{ar ? "التالي" : "Next"}</button>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3 last:border-0">
      <span className="text-sm font-medium text-ink-500">{label}</span>
      <span className="text-end text-sm font-semibold text-ink-900">{value}</span>
    </div>
  );
}
