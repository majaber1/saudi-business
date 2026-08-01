"use client";

import { useLanguage } from "@/components/LanguageProvider";

const FAQ: { q: { ar: string; en: string }; a: { ar: string; en: string } }[] = [
  {
    q: { ar: "ما هي منصّة سعودي بزنس؟", en: "What is Saudi Business?" },
    a: {
      ar: "منصّة لإعداد دراسات الجدوى والتحليل المالي ومطابقة برامج التمويل السعودية، تدعم العربية والإنجليزية بالكامل.",
      en: "A platform for feasibility studies, financial analysis, and Saudi funding-program matching, with full Arabic and English support.",
    },
  },
  {
    q: { ar: "كيف أبدأ دراسة جدوى؟", en: "How do I start a feasibility study?" },
    a: {
      ar: "أنشئ حسابًا، ثم استخدم معالج دراسة الجدوى الذي ينتهي بتقرير قابل للتصدير. (المعالج قيد التطوير حاليًا.)",
      en: "Create an account, then use the feasibility wizard that ends with an exportable report. (The wizard is currently in development.)",
    },
  },
  {
    q: { ar: "هل التمويل مضمون؟", en: "Is funding guaranteed?" },
    a: {
      ar: "لا. المطابقة إرشادية فقط، والأهلية والشروط تُحدّدها الجهات الرسمية لكل برنامج.",
      en: "No. Matching is indicative only; eligibility and terms are determined by each program's official body.",
    },
  },
  {
    q: { ar: "هل بياناتي محفوظة بشكل دائم؟", en: "Is my data stored persistently?" },
    a: {
      ar: "عند تفعيل قاعدة بيانات الإنتاج تُحفظ البيانات بشكل دائم؛ وفي البيئة التجريبية تعمل المنصّة بوضع مؤقت واضح.",
      en: "When the production database is enabled, data is stored persistently; in the demo environment the platform runs in a clearly-labeled temporary mode.",
    },
  },
];

export default function HelpPage() {
  const { locale } = useLanguage();
  const pick = (b: { ar: string; en: string }) => (locale === "ar" ? b.ar : b.en);

  return (
    <main className="container-page py-14">
      <h1 className="text-3xl font-semibold text-ink-900">
        {locale === "ar" ? "مركز المساعدة" : "Help Center"}
      </h1>
      <p className="mt-3 max-w-3xl text-ink-700">
        {locale === "ar"
          ? "أسئلة شائعة حول استخدام المنصّة. للمزيد من الدعم يمكنك التواصل عبر مستودع المشروع."
          : "Frequently asked questions about using the platform. For further support, reach out via the project repository."}
      </p>

      <div className="mt-8 space-y-4">
        {FAQ.map((item, i) => (
          <details
            key={i}
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <summary className="cursor-pointer list-none font-medium text-ink-900 marker:content-['']">
              {pick(item.q)}
            </summary>
            <p className="mt-3 text-sm text-ink-700">{pick(item.a)}</p>
          </details>
        ))}
      </div>
    </main>
  );
}
