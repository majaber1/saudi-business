"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { getToken, createProject } from "@/lib/api";

export default function NewBusinessPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const router = useRouter();
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [investment, setInvestment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    if (!name.trim()) {
      setError(ar ? "اسم العمل مطلوب" : "Business name is required");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const project = await createProject(token, {
        name: name.trim(),
        industry: industry.trim() || "other",
        investment: investment ? Number(investment) : 0,
      });
      router.push(`/businesses/${project.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : (ar ? "حدث خطأ" : "Something went wrong"));
      setSubmitting(false);
    }
  }

  return (
    <div className="px-4 py-8 lg:px-8" data-testid="new-business-page">
      <nav className="mb-6 text-sm text-ink-500">
        <Link href="/businesses" className="hover:text-brand-600">{ar ? "أعمالي" : "My Businesses"}</Link>
        <span className="mx-2">/</span>
        <span className="font-medium text-ink-800">{ar ? "عمل جديد" : "New Business"}</span>
      </nav>

      <div className="mx-auto max-w-xl">
        <h1 className="text-2xl font-bold text-ink-900">{ar ? "إنشاء عمل جديد" : "Create New Business"}</h1>
        <p className="mt-2 text-sm text-ink-500">
          {ar ? "أضف عملك الجديد لبدء رحلة التقييم والدراسة" : "Add your new business to start the evaluation journey"}
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label htmlFor="biz-name" className="block text-sm font-semibold text-ink-800">
              {ar ? "اسم العمل" : "Business Name"} *
            </label>
            <input
              id="biz-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={ar ? "مثال: مقهى الخبراء" : "e.g. Expert Consulting"}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-400"
              data-testid="input-business-name"
            />
          </div>

          <div>
            <label htmlFor="biz-industry" className="block text-sm font-semibold text-ink-800">
              {ar ? "القطاع" : "Industry / Sector"}
            </label>
            <input
              id="biz-industry"
              type="text"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder={ar ? "مثال: تقنية، مطاعم، عقارات" : "e.g. Technology, F&B, Real Estate"}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-400"
              data-testid="input-business-industry"
            />
          </div>

          <div>
            <label htmlFor="biz-investment" className="block text-sm font-semibold text-ink-800">
              {ar ? "الاستثمار المقدّر (ريال)" : "Estimated Investment (SAR)"}
            </label>
            <input
              id="biz-investment"
              type="number"
              min="0"
              value={investment}
              onChange={(e) => setInvestment(e.target.value)}
              placeholder={ar ? "اختياري" : "Optional"}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-400"
              data-testid="input-business-investment"
            />
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700" data-testid="form-error">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              data-testid="submit-new-business"
              className="rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? (ar ? "جارٍ الإنشاء..." : "Creating...") : (ar ? "إنشاء العمل" : "Create Business")}
            </button>
            <Link
              href="/businesses"
              className="rounded-xl border border-slate-200 px-6 py-3 text-sm font-semibold text-ink-700 hover:border-brand-300"
            >
              {ar ? "إلغاء" : "Cancel"}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
