"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { login, me, saveToken } from "@/lib/api";

const copy = {
  ar: {
    title: "تسجيل الدخول",
    email: "البريد الإلكتروني",
    password: "كلمة المرور",
    submit: "دخول",
    loading: "جارٍ الدخول...",
    noAccount: "ليس لديك حساب؟",
    register: "إنشاء حساب",
    success: "تم تسجيل الدخول بنجاح، مرحبًا",
    demoNote:
      "بيئة تجريبية: يتطلب الدخول تشغيل الواجهة البرمجية وضبط NEXT_PUBLIC_API_BASE_URL.",
  },
  en: {
    title: "Sign in",
    email: "Email",
    password: "Password",
    submit: "Sign in",
    loading: "Signing in...",
    noAccount: "No account yet?",
    register: "Create an account",
    success: "Signed in successfully, welcome",
    demoNote:
      "Demo environment: sign-in requires the API running and NEXT_PUBLIC_API_BASE_URL set.",
  },
};

export default function LoginPage() {
  const { locale } = useLanguage();
  const c = copy[locale];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profileName, setProfileName] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { access_token } = await login(email, password);
      saveToken(access_token);
      const profile = await me(access_token);
      setProfileName(profile.full_name || profile.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container-page py-16">
      <div className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-ink-900">{c.title}</h1>

        {profileName ? (
          <p className="mt-6 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">
            {c.success} {profileName}.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block text-sm">
              <span className="text-ink-700">{c.email}</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-ink-700">{c.password}</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
              />
            </label>
            {error && (
              <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-brand-600 px-4 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? c.loading : c.submit}
            </button>
          </form>
        )}

        <p className="mt-6 text-sm text-ink-700">
          {c.noAccount}{" "}
          <Link href="/register" className="font-medium text-brand-600 hover:underline">
            {c.register}
          </Link>
        </p>
        <p className="mt-4 text-xs text-ink-500">{c.demoNote}</p>
      </div>
    </main>
  );
}
