"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { requestPasswordReset } from "@/lib/api";

export default function ForgotPasswordPage() {
  const { locale } = useLanguage();
  const ar = locale === "ar";
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await requestPasswordReset(email); setDone(true); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Request failed"); }
    finally { setBusy(false); }
  }
  return <main className="container-page py-16"><section className="mx-auto max-w-md rounded-2xl border bg-white p-8 shadow-card">
    <h1 className="text-2xl font-bold">{ar ? "استعادة كلمة المرور" : "Reset your password"}</h1>
    {done ? <p role="status" className="mt-5 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">{ar ? "إذا كان الحساب موجودًا فسيصلك رابط آمن لإعادة التعيين." : "If the account exists, a secure reset link has been sent."}</p> : <form onSubmit={submit} className="mt-6 space-y-4"><label className="block text-sm"><span>{ar ? "البريد الإلكتروني" : "Email"}</span><input className="mt-1 w-full rounded-lg border px-3 py-2 focus:ring-2 focus:ring-brand-200" type="email" required value={email} onChange={e => setEmail(e.target.value)}/></label>{error && <p className="text-sm text-red-700">{error}</p>}<button disabled={busy} className="w-full rounded-lg bg-brand-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60">{busy ? (ar ? "جارٍ الإرسال…" : "Sending…") : (ar ? "إرسال الرابط" : "Send reset link")}</button></form>}
    <Link href="/login" className="mt-5 block text-center text-sm text-brand-700 hover:underline">{ar ? "العودة لتسجيل الدخول" : "Back to sign in"}</Link>
  </section></main>;
}
