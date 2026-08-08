"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { confirmEmailVerification } from "@/lib/api";

export default function VerifyEmailPage() {
  const { locale } = useLanguage(); const ar = locale === "ar";
  const [state, setState] = useState<"loading" | "done" | "error">("loading");
  useEffect(() => { const token = new URLSearchParams(window.location.search).get("token"); if (!token) { setState("error"); return; } confirmEmailVerification(token).then(() => setState("done")).catch(() => setState("error")); }, []);
  return <main className="container-page py-16"><section className="mx-auto max-w-md rounded-2xl border bg-white p-8 text-center shadow-card"><h1 className="text-2xl font-bold">{ar ? "تأكيد البريد الإلكتروني" : "Email verification"}</h1><p role="status" className="mt-5 text-ink-700">{state === "loading" ? (ar ? "جارٍ التحقق…" : "Verifying…") : state === "done" ? (ar ? "تم تأكيد بريدك الإلكتروني بنجاح." : "Your email has been verified.") : (ar ? "الرابط غير صالح أو منتهي الصلاحية." : "This link is invalid or expired.")}</p>{state !== "loading" && <Link href="/login" className="mt-5 inline-block font-medium text-brand-700 hover:underline">{ar ? "تسجيل الدخول" : "Sign in"}</Link>}</section></main>;
}
