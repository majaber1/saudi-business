"use client";

import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { ServiceHeader } from "@/components/ui/ServiceHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Stepper } from "@/components/ui/Stepper";

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

export default function ProposalBuilderPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [mode, setMode] = useState<"list" | "new">("list");
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

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

          {currentStep >= 1 && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
              <h2 className="text-xl font-bold text-ink-900">
                {currentStep === 1 ? (ar ? "العميل / المستلم" : "Client / Recipient") :
                 currentStep === 2 ? (ar ? "النطاق والحل" : "Scope & Solution") :
                 currentStep === 3 ? (ar ? "التسعير والجدول الزمني" : "Pricing & Timeline") :
                 (ar ? "المراجعة والتصدير" : "Review & Export")}
              </h2>
              <div className="mt-6 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-12 text-center">
                <span className="mb-3 block text-4xl opacity-50">🚧</span>
                <p className="text-sm text-ink-600">
                  {ar ? "هذه الخطوة قيد التطوير. سيتم إضافة حقول الإدخال الكاملة قريبًا." : "This step is under development. Full input fields will be added soon."}
                </p>
              </div>

              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                  className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-ink-700 hover:border-brand-500"
                >
                  {ar ? "السابق" : "Previous"}
                </button>
                {currentStep < 4 ? (
                  <button
                    onClick={() => setCurrentStep(currentStep + 1)}
                    className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700"
                  >
                    {ar ? "التالي" : "Next"}
                  </button>
                ) : (
                  <button className="rounded-xl bg-gold-500 px-5 py-3 text-sm font-bold text-brand-900 hover:bg-gold-400">
                    {ar ? "تصدير PDF" : "Export PDF"}
                  </button>
                )}
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

        <EmptyState
          icon="📝"
          title={ar ? "لا توجد عروض سابقة" : "No previous proposals"}
          description={ar ? "ابدأ بإنشاء عرضك التجاري الأول." : "Start by creating your first business proposal."}
          actionLabel={ar ? "عرض جديد" : "New proposal"}
          onAction={() => setMode("new")}
        />

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
