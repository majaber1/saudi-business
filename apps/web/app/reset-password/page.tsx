"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { resetPassword } from "@/lib/api";

export default function ResetPasswordPage() {
  const { locale } = useLanguage(); const ar = locale === "ar";
  const [token, setToken] = useState(""); const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false); const [done, setDone] = useState(false); const [error, setError] = useState("");
  useEffect(() => setToken(new URLSearchParams(window.location.search).get("token") || ""), []);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { await resetPassword(token, password); setDone(true); } catch (cause) { setError(cause instanceof Error ? cause.message : "Request failed"); } finally { setBusy(false); } }
  return <main className="container-page py-16"><section className="mx-auto max-w-md rounded-2xl border bg-white p-8 shadow-card"><h1 className="text-2xl font-bold">{ar ? "تعيين كلمة مرور جديدة" : "Choose a new password"}</h1>{!token ? <p className="mt-5 text-red-700">{ar ? "الرابط غير صالح." : "This reset link is invalid."}</p> : done ? <div className="mt-5"><p role="status" className="rounded-lg bg-emerald-50 p-4 text-emerald-800">{ar ? "تم تحديث كلمة المرور." : "Your password has been updated."}</p><Link href="/login" className="mt-4 block text-center text-brand-700 hover:underline">{ar ? "تسجيل الدخول" : "Sign in"}</Link></div> : <form onSubmit={submit} className="mt-6 space-y-4"><label className="block text-sm"><span>{ar ? "كلمة المرور الجديدة" : "New password"}</span><input type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)} className="mt-1 w-full rounded-lg border px-3 py-2 focus:ring-2 focus:ring-brand-200"/></label>{error && <p className="text-sm text-red-700">{error}</p>}<button disabled={busy} className="w-full rounded-lg bg-brand-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60">{busy ? (ar ? "جارٍ الحفظ…" : "Saving…") : (ar ? "حفظ كلمة المرور" : "Save password")}</button></form>}</section></main>;
}
