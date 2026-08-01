"use client";

import { FeaturePage } from "@/components/FeaturePage";

export default function AuctionsPage() {
  return (
    <FeaturePage
      title={{ ar: "مزاد الأعمال", en: "Business Auctions" }}
      intro={{
        ar: "منصّة للإعلان عن المشاريع والأصول التجارية المعروضة للبيع، وربط البائعين بالمشترين المهتمين.",
        en: "A marketplace to list businesses and commercial assets for sale, connecting sellers with interested buyers.",
      }}
      status={{
        ar: "الواجهة جاهزة، وسيتم تفعيل إنشاء المزادات وتسجيل العروض (بدون أي معالجة دفع أو تسوية).",
        en: "The interface is ready; auction creation and bid recording will be enabled (with no payment processing or settlement).",
      }}
      bullets={[
        { ar: "إنشاء إعلان مزاد للنشاط التجاري", en: "Create a business auction listing" },
        { ar: "تسجيل العروض والاهتمامات", en: "Record bids and expressions of interest" },
        { ar: "التواصل بين البائع والمشتري", en: "Seller–buyer communication" },
        { ar: "أرشيف المزادات المنتهية", en: "Archive of closed auctions" },
      ]}
      disclaimer={{
        ar: "تنبيه قانوني: المنصّة توفّر خدمة إعلانية وربط فقط، ولا تتضمن معالجة مدفوعات أو ضمان أو تسوية ملزمة. جميع الاتفاقيات تتم مباشرة بين الأطراف وعلى مسؤوليتهم، ويُنصح بالاستعانة بمستشار قانوني.",
        en: "Legal notice: this platform provides listing and connection services only. It does not include payment processing, escrow, or legally binding settlement. All agreements are made directly between parties at their own responsibility; consulting a legal advisor is recommended.",
      }}
    />
  );
}
