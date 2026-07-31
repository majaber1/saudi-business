export type Locale = "ar" | "en";

export const LOCALES: Locale[] = ["ar", "en"];
export const DEFAULT_LOCALE: Locale = "ar";

export const dir = (locale: Locale): "rtl" | "ltr" => (locale === "ar" ? "rtl" : "ltr");

type Dict = {
  brand: string;
  tagline: string;
  nav: { home: string; funding: string; ideas: string; franchises: string; auctions: string; multazim: string; help: string; login: string; register: string };
  hero: { title: string; subtitle: string; cta: string; secondary: string };
  features: { title: string; items: { title: string; body: string }[] };
  status: { title: string; body: string };
  footer: { rights: string; disclaimer: string };
};

export const dictionaries: Record<Locale, Dict> = {
  ar: {
    brand: "سعودي بزنس",
    tagline: "من الفكرة إلى قرار الاستثمار",
    nav: {
      home: "الرئيسية",
      funding: "برامج التمويل",
      ideas: "بنك الأفكار",
      franchises: "فرص الامتياز",
      auctions: "المزاد",
      multazim: "ملتزم",
      help: "مركز المساعدة",
      login: "تسجيل الدخول",
      register: "إنشاء حساب",
    },
    hero: {
      title: "منصّة سعودية لدراسات الجدوى وقرارات الاستثمار",
      subtitle: "محرّك مالي حقيقي، ومطابقة شفافة لبرامج التمويل السعودية، وتقارير احترافية بالعربية والإنجليزية.",
      cta: "ابدأ دراسة جدوى",
      secondary: "استكشف برامج التمويل",
    },
    features: {
      title: "ماذا تقدّم المنصّة",
      items: [
        { title: "دراسة الجدوى", body: "معالج متعدّد الخطوات ينتهي بتقرير قابل للتصدير PDF و Word." },
        { title: "التحليل المالي", body: "ROI و NPV و IRR وفترة الاسترداد ونقطة التعادل وتحليل الحساسية." },
        { title: "مطابقة التمويل", body: "مطابقة قابلة للتفسير مع برامج مثل منشآت و NTDP و كفالة." },
      ],
    },
    status: {
      title: "قيد التطوير",
      body: "الواجهة الأمامية قيد البناء تدريجيًا فوق واجهة برمجية تم التحقق منها (مصادقة، وثبات بيانات، محرّكات مالية).",
    },
    footer: {
      rights: "جميع الحقوق محفوظة",
      disclaimer: "المنصّة أداة مساعدة ولا تُعدّ استشارة قانونية أو مالية أو ضريبية.",
    },
  },
  en: {
    brand: "Saudi Business",
    tagline: "From idea to investment decision",
    nav: {
      home: "Home",
      funding: "Funding Programs",
      ideas: "Idea Bank",
      franchises: "Franchises",
      auctions: "Auctions",
      multazim: "Multazim",
      help: "Help Center",
      login: "Log in",
      register: "Sign up",
    },
    hero: {
      title: "A Saudi platform for feasibility studies and investment decisions",
      subtitle: "A real financial engine, transparent Saudi funding-program matching, and professional reports in Arabic and English.",
      cta: "Start a feasibility study",
      secondary: "Explore funding programs",
    },
    features: {
      title: "What the platform offers",
      items: [
        { title: "Feasibility Study", body: "A multi-step wizard ending in an exportable PDF and Word report." },
        { title: "Financial Analysis", body: "ROI, NPV, IRR, payback, break-even, and sensitivity analysis." },
        { title: "Funding Matching", body: "Explainable matching against programs like Monsha'at, NTDP, and Kafalah." },
      ],
    },
    status: {
      title: "In progress",
      body: "The frontend is being built incrementally on top of a CI-verified API (auth, persistence, financial engines).",
    },
    footer: {
      rights: "All rights reserved",
      disclaimer: "This platform is a decision-support tool, not legal, financial, or tax advice.",
    },
  },
};
