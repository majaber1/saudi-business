"use client";

import { FeaturePage } from "@/components/FeaturePage";

export default function MultazimPage() {
  return (
    <FeaturePage
      title={{ ar: "ملتزم — الامتثال التنظيمي", en: "Multazim — Regulatory Compliance" }}
      intro={{
        ar: "وحدة ملتزم تساعد رواد الأعمال على تقييم التزام مشاريعهم بالمتطلبات التنظيمية السعودية عبر تقييم ذاتي منظّم ولوحة متابعة.",
        en: "The Multazim module helps entrepreneurs assess their project's compliance with Saudi regulatory requirements through a structured self-assessment and tracking dashboard.",
      }}
      status={{
        ar: "تم تحديد مشروع ملتزم المصدر (multazim-ai-mvp)، ويجري دمج نموذج بيانات المتطلبات والتقييم داخل هذه المنصّة تدريجيًا مع الحفاظ على التحقق عبر الاختبارات.",
        en: "The source Multazim project (multazim-ai-mvp) has been identified, and its requirement/assessment data model is being integrated into this platform incrementally while preserving test verification.",
      }}
      bullets={[
        { ar: "تقييم ذاتي للامتثال التنظيمي", en: "Regulatory compliance self-assessment" },
        { ar: "قائمة متطلبات حسب النشاط", en: "Requirements checklist by activity" },
        { ar: "لوحة متابعة حالة الالتزام", en: "Compliance status dashboard" },
        { ar: "ربط النتائج بدراسة الجدوى", en: "Link results to the feasibility study" },
      ]}
      disclaimer={{
        ar: "المحتوى التنظيمي إرشادي ولا يُغني عن الرجوع إلى الجهات الرسمية والمستشار القانوني؛ وتُوثّق مصادر المتطلبات وتواريخ تحققها.",
        en: "Regulatory content is indicative and does not replace consulting official bodies and legal counsel; requirement sources and verification dates are documented.",
      }}
    />
  );
}
