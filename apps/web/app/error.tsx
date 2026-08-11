"use client";

import { useLanguage } from "@/components/LanguageProvider";

export default function AppError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  return (
    <section className="container-page grid min-h-[60vh] place-items-center py-16 text-center">
      <div className="max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-card">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-red-50 font-bold text-red-700">!</span>
        <h1 className="mt-5 text-2xl font-bold text-ink-900">{ar ? "حدث خطأ غير متوقع" : "Something went wrong"}</h1>
        <p className="mt-3 text-sm leading-6 text-ink-600">{ar ? "لم نفقد بياناتك. حاول تحميل هذه الصفحة مرة أخرى." : "Your data was not discarded. Try loading this page again."}</p>
        <button onClick={reset} className="mt-6 rounded-xl bg-brand-600 px-5 py-3 text-sm font-bold text-white hover:bg-brand-700">{ar ? "إعادة المحاولة" : "Try again"}</button>
      </div>
    </section>
  );
}
