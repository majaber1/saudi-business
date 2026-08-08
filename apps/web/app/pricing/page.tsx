"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { submitLead } from "@/lib/api";

type PlanKey = "starter" | "professional" | "enterprise";

const copy = {
  ar: {
    title: "الأسعار",
    subtitle: "اختر الباقة المناسبة لحجم أعمالك. لا تتم أي عمليات دفع عبر هذه المنصة — فريق المبيعات يتواصل معك مباشرة.",
    perMonth: "شهريًا",
    contactSales: "تواصل مع المبيعات",
    mostPopular: "الأكثر طلبًا",
    plans: {
      starter: {
        name: "أساسي",
        price: "مجانًا",
        audience: "لرواد الأعمال ودراسة أول مشروع",
        features: ["دراسة جدوى واحدة نشطة", "التحليل المالي الكامل (ROI/NPV/IRR)", "مطابقة برامج التمويل", "تقرير PDF واحد شهريًا"],
      },
      professional: {
        name: "احترافي",
        price: "٢٤٩ ر.س",
        audience: "للمستشارين وأصحاب عدة مشاريع",
        features: ["دراسات جدوى غير محدودة", "تقارير PDF و Word غير محدودة", "أرشفة ومتابعة المشاريع", "دعم عبر البريد الإلكتروني"],
      },
      enterprise: {
        name: "المؤسسات",
        price: "تواصل معنا",
        audience: "للبنوك والجهات الحكومية والمستثمرين المؤسسيين",
        features: ["عدد مستخدمين غير محدود وصلاحيات RBAC", "تكامل عبر MCP/API", "نطاق مخصص واتفاقية مستوى خدمة", "مدير حساب مخصص"],
      },
    },
    form: {
      title: "اطلب الوصول",
      name: "الاسم الكامل",
      email: "البريد الإلكتروني",
      company: "الشركة (اختياري)",
      message: "أخبرنا عن احتياجك (اختياري)",
      submit: "إرسال الطلب",
      sending: "جارٍ الإرسال...",
      successPersisted: "تم استلام طلبك. سيتواصل معك فريقنا قريبًا.",
      successDemo: "تم استلام النموذج (بيئة تجريبية — لم يُحفظ الطلب لعدم توفر قاعدة بيانات).",
      error: "تعذّر إرسال الطلب. حاول مرة أخرى.",
      noPayment: "لا حاجة لبطاقة ائتمانية الآن. هذه المنصة لا تُجري أي تحويلات مالية.",
    },
  },
  en: {
    title: "Pricing",
    subtitle: "Pick the plan that fits your business. No payment is processed on this platform — our sales team reaches out directly.",
    perMonth: "/month",
    contactSales: "Talk to sales",
    mostPopular: "Most popular",
    plans: {
      starter: {
        name: "Starter",
        price: "Free",
        audience: "For entrepreneurs studying their first project",
        features: ["1 active feasibility study", "Full financial analysis (ROI/NPV/IRR)", "Funding program matching", "1 PDF report / month"],
      },
      professional: {
        name: "Professional",
        price: "SAR 249",
        audience: "For consultants and multi-project owners",
        features: ["Unlimited feasibility studies", "Unlimited PDF & Word reports", "Project archive & tracking", "Email support"],
      },
      enterprise: {
        name: "Enterprise",
        price: "Contact us",
        audience: "For banks, government bodies, and institutional investors",
        features: ["Unlimited seats with RBAC", "MCP/API integration", "Custom domain & SLA", "Dedicated account manager"],
      },
    },
    form: {
      title: "Request access",
      name: "Full name",
      email: "Email",
      company: "Company (optional)",
      message: "Tell us what you need (optional)",
      submit: "Send request",
      sending: "Sending...",
      successPersisted: "Your request was received. Our team will reach out soon.",
      successDemo: "Form received (demo environment — not saved, no database configured).",
      error: "Couldn't send your request. Please try again.",
      noPayment: "No credit card needed right now. This platform does not process any financial transfers.",
    },
  },
};

const PLAN_ORDER: PlanKey[] = ["starter", "professional", "enterprise"];

export default function PricingPage() {
  const { locale } = useLanguage();
  const c = copy[locale];

  const [selectedPlan, setSelectedPlan] = useState<PlanKey>("professional");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<"persisted" | "demo" | "error" | null>(null);

  function pickPlan(plan: PlanKey) {
    setSelectedPlan(plan);
    document.getElementById("request-access")?.scrollIntoView({ behavior: "smooth" });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      const res = await submitLead({
        full_name: name,
        email,
        company: company || undefined,
        message: message || undefined,
        plan: selectedPlan,
        intent: selectedPlan === "enterprise" ? "enterprise" : "subscribe",
      });
      setResult(res.persisted ? "persisted" : "demo");
    } catch {
      setResult("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container-page py-14">
      <h1 className="text-3xl font-bold tracking-tight text-ink-900">{c.title}</h1>
      <p className="mt-2 max-w-2xl text-ink-600">{c.subtitle}</p>

      <div className="mt-10 grid gap-6 lg:grid-cols-3">
        {PLAN_ORDER.map((key) => {
          const plan = c.plans[key];
          const popular = key === "professional";
          return (
            <div
              key={key}
              className={
                "flex flex-col rounded-2xl border bg-white p-6 shadow-card " +
                (popular ? "border-brand-500 ring-1 ring-brand-500" : "border-slate-200")
              }
            >
              {popular && (
                <span className="mb-3 inline-flex w-fit rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
                  {c.mostPopular}
                </span>
              )}
              <h2 className="text-lg font-semibold text-ink-900">{plan.name}</h2>
              <p className="mt-1 text-sm text-ink-500">{plan.audience}</p>
              <p className="mt-4 text-3xl font-bold text-ink-900">
                {plan.price}
                {key === "professional" && <span className="text-sm font-normal text-ink-500"> {c.perMonth}</span>}
              </p>
              <ul className="mt-6 flex-1 space-y-2.5 text-sm text-ink-700">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => pickPlan(key)}
                className={
                  "mt-6 rounded-lg px-4 py-2.5 text-sm font-medium transition " +
                  (popular
                    ? "bg-brand-600 text-white hover:bg-brand-700"
                    : "border border-slate-300 text-ink-800 hover:border-brand-500 hover:text-brand-600")
                }
              >
                {c.contactSales}
              </button>
            </div>
          );
        })}
      </div>

      <div id="request-access" className="mx-auto mt-16 max-w-lg scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-8 shadow-card">
        <h2 className="text-xl font-semibold text-ink-900">{c.form.title}</h2>

        {result === "persisted" || result === "demo" ? (
          <p className="mt-6 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">
            {result === "persisted" ? c.form.successPersisted : c.form.successDemo}
          </p>
        ) : (
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block text-sm">
              <span className="text-ink-700">{c.form.name}</span>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-700">{c.form.email}</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-700">{c.form.company}</span>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-700">{c.form.message}</span>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            {result === "error" && (
              <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{c.form.error}</p>
            )}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-brand-600 px-4 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? c.form.sending : c.form.submit}
            </button>
            <p className="text-xs text-ink-500">{c.form.noPayment}</p>
          </form>
        )}
      </div>
    </main>
  );
}
