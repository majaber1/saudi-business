"use client";

import { useLanguage } from "@/components/LanguageProvider";

// Program NAMES only. No amounts, eligibility, or deadlines are shown here
// because those must be verified against official sources before display.
const PROGRAMS: { ar: string; en: string; source: string }[] = [
  { ar: "منشآت", en: "Monshaat (SME Authority)", source: "https://www.monshaat.gov.sa" },
  { ar: "بنك التنمية الاجتماعية", en: "Social Development Bank", source: "https://www.sdb.gov.sa" },
  { ar: "صندوق التنمية الصناعية (SIDF)", en: "Saudi Industrial Development Fund", source: "https://www.sidf.gov.sa" },
  { ar: "برنامج تطوير التقنية الوطنية (NTDP)", en: "National Technology Development Program", source: "https://ntdp.gov.sa" },
  { ar: "كفالة", en: "Kafalah (SME Loan Guarantee)", source: "https://kafalah.gov.sa" },
];

const copy = {
  ar: {
    title: "برامج التمويل السعودية",
    intro:
      "مطابقة شفافة بين مشروعك وبرامج التمويل الحكومية وشبه الحكومية. تُعرض أسماء البرامج فقط في هذه المرحلة؛ وتُضاف شروط الأهلية والمبالغ بعد التحقق من المصادر الرسمية.",
    unverified: "يتطلب التحقق",
    officialSource: "المصدر الرسمي",
    disclaimer:
      "هذه القائمة إرشادية ولا تُعدّ عرضًا للتمويل. راجع الجهة الرسمية لكل برنامج للتأكد من الأهلية والشروط الحالية.",
  },
  en: {
    title: "Saudi Funding Programs",
    intro:
      "Transparent matching between your project and government and quasi-government funding programs. Only program names are shown at this stage; eligibility and amounts are added after verification against official sources.",
    unverified: "Requires verification",
    officialSource: "Official source",
    disclaimer:
      "This list is indicative and is not a funding offer. Check each program's official body for current eligibility and terms.",
  },
};

export default function FundingPage() {
  const { locale } = useLanguage();
  const c = copy[locale];

  return (
    <main className="container-page py-14">
      <h1 className="text-3xl font-semibold text-ink-900">{c.title}</h1>
      <p className="mt-3 max-w-3xl text-ink-700">{c.intro}</p>

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {PROGRAMS.map((p) => (
          <li
            key={p.en}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold text-ink-900">
                {locale === "ar" ? p.ar : p.en}
              </h2>
              <span className="shrink-0 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
                {c.unverified}
              </span>
            </div>
            <a
              href={p.source}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-block text-sm text-brand-600 hover:underline"
            >
              {c.officialSource}
            </a>
          </li>
        ))}
      </ul>

      <p className="mt-8 max-w-3xl text-xs text-ink-500">{c.disclaimer}</p>
    </main>
  );
}
