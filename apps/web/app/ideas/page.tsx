"use client";

import { FeaturePage } from "@/components/FeaturePage";

export default function IdeasPage() {
  return (
    <FeaturePage
      title={{ ar: "بنك الأفكار", en: "Idea Bank" }}
      intro={{
        ar: "مكتبة من أفكار المشاريع القابلة للتنفيذ في السوق السعودي، مع إمكانية تحويل أي فكرة إلى دراسة جدوى بضغطة واحدة.",
        en: "A library of actionable business ideas for the Saudi market, with the ability to turn any idea into a feasibility study in one click.",
      }}
      status={{
        ar: "الواجهة جاهزة، وسيتم ربط المحتوى بقاعدة البيانات وتفعيل التصفية حسب القطاع وحجم رأس المال.",
        en: "The interface is ready; content will be connected to the database with filtering by sector and capital size.",
      }}
      bullets={[
        { ar: "تصفية حسب القطاع والمدينة", en: "Filter by sector and city" },
        { ar: "تقدير مبدئي لرأس المال المطلوب", en: "Indicative required-capital estimate" },
        { ar: "تحويل الفكرة إلى دراسة جدوى", en: "Convert an idea into a feasibility study" },
        { ar: "حفظ الأفكار المفضّلة", en: "Save favorite ideas" },
      ]}
      disclaimer={{
        ar: "الأفكار المعروضة إرشادية ولا تضمن نجاح المشروع؛ يُنصح بإجراء دراسة جدوى كاملة.",
        en: "Listed ideas are indicative and do not guarantee success; a full feasibility study is recommended.",
      }}
    />
  );
}
