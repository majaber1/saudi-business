"use client";

import { FeaturePage } from "@/components/FeaturePage";

export default function FranchisesPage() {
  return (
    <FeaturePage
      title={{ ar: "فرص الامتياز التجاري", en: "Franchise Opportunities" }}
      intro={{
        ar: "استكشف فرص الامتياز التجاري المتاحة، وقارن بينها، واطلب دراسة جدوى مخصّصة لأي علامة تجارية.",
        en: "Explore available franchise opportunities, compare them, and request a tailored feasibility study for any brand.",
      }}
      status={{
        ar: "الواجهة جاهزة، وسيتم ربط قوائم العلامات التجارية بقاعدة البيانات مع لوحة تحكّم لمانحي الامتياز.",
        en: "The interface is ready; brand listings will be connected to the database with a franchisor dashboard.",
      }}
      bullets={[
        { ar: "بطاقات تعريفية للعلامات التجارية", en: "Brand profile cards" },
        { ar: "مقارنة رسوم الامتياز والدعم", en: "Compare franchise fees and support" },
        { ar: "طلب دراسة جدوى للفرع", en: "Request a branch feasibility study" },
        { ar: "لوحة تحكّم لمانح الامتياز", en: "Franchisor management dashboard" },
      ]}
      disclaimer={{
        ar: "المعلومات المعروضة يقدّمها مانحو الامتياز وتتطلب التحقق المباشر قبل اتخاذ أي التزام.",
        en: "Displayed information is provided by franchisors and requires direct verification before any commitment.",
      }}
    />
  );
}
