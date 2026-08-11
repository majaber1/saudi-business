"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { changePassword, getToken, me, updateProfile, type UserProfile } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

const copy = {
  ar: {
    title: "حسابي", intro: "حدّث معلوماتك أو غيّر كلمة المرور بأمان.", login: "سجّل الدخول لإدارة حسابك.",
    name: "الاسم الكامل", email: "البريد الإلكتروني", role: "نوع الحساب", verified: "البريد موثّق", notVerified: "البريد غير موثّق",
    save: "حفظ المعلومات", saving: "جارٍ الحفظ...", saved: "تم حفظ معلوماتك.",
    passwordTitle: "تغيير كلمة المرور", current: "كلمة المرور الحالية", next: "كلمة المرور الجديدة", confirm: "تأكيد كلمة المرور الجديدة",
    change: "تغيير كلمة المرور", changing: "جارٍ التغيير...", changed: "تم تغيير كلمة المرور.", mismatch: "كلمتا المرور الجديدتان غير متطابقتين.",
  },
  en: {
    title: "My account", intro: "Update your details or change your password securely.", login: "Sign in to manage your account.",
    name: "Full name", email: "Email", role: "Account type", verified: "Email verified", notVerified: "Email not verified",
    save: "Save details", saving: "Saving...", saved: "Your details were saved.",
    passwordTitle: "Change password", current: "Current password", next: "New password", confirm: "Confirm new password",
    change: "Change password", changing: "Changing...", changed: "Your password was changed.", mismatch: "The new passwords do not match.",
  },
};

export default function AccountPage() {
  const { locale } = useLanguage();
  const c = copy[locale];
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [name, setName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState<"profile" | "password" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    me(token).then((data) => { setProfile(data); setName(data.full_name || ""); }).catch(() => setProfile(null));
  }, []);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault(); const token = getToken(); if (!token) return;
    setBusy("profile"); setError(null); setMessage(null);
    try { const updated = await updateProfile(token, { full_name: name, locale }); setProfile(updated); setMessage(c.saved); }
    catch (err) { setError(err instanceof Error ? err.message : String(err)); }
    finally { setBusy(null); }
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault(); const token = getToken(); if (!token) return;
    if (newPassword !== confirmPassword) return setError(c.mismatch);
    setBusy("password"); setError(null); setMessage(null);
    try { await changePassword(token, currentPassword, newPassword); setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); setMessage(c.changed); }
    catch (err) { setError(err instanceof Error ? err.message : String(err)); }
    finally { setBusy(null); }
  }

  if (!getToken()) return <main className="container-page py-16"><div className="mx-auto max-w-xl rounded-2xl border bg-white p-8"><h1 className="text-2xl font-bold">{c.title}</h1><p className="mt-3 text-ink-600">{c.login}</p><Link href="/login" className="mt-6 inline-flex rounded-lg bg-brand-600 px-5 py-2.5 text-white">{locale === "ar" ? "تسجيل الدخول" : "Sign in"}</Link></div></main>;

  return <main className="container-page py-12"><div className="mx-auto max-w-2xl space-y-6">
    <header><h1 className="text-3xl font-bold text-ink-900">{c.title}</h1><p className="mt-2 text-ink-600">{c.intro}</p></header>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    {message && <p className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">{message}</p>}
    <form onSubmit={saveProfile} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <label className="block text-sm text-ink-700">{c.name}<input value={name} onChange={(e) => setName(e.target.value)} maxLength={200} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
      <div className="grid gap-4 sm:grid-cols-2"><div><p className="text-xs text-ink-500">{c.email}</p><p className="mt-1 font-medium">{profile?.email}</p></div><div><p className="text-xs text-ink-500">{c.role}</p><p className="mt-1 font-medium">{profile?.role_key}</p></div></div>
      <p className={"text-sm " + (profile?.email_verified ? "text-emerald-700" : "text-amber-700")}>{profile?.email_verified ? c.verified : c.notVerified}</p>
      <button disabled={busy !== null} className="rounded-lg bg-brand-600 px-5 py-2.5 font-medium text-white disabled:opacity-60">{busy === "profile" ? c.saving : c.save}</button>
    </form>
    <form onSubmit={savePassword} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold">{c.passwordTitle}</h2>
      {[[c.current,currentPassword,setCurrentPassword],[c.next,newPassword,setNewPassword],[c.confirm,confirmPassword,setConfirmPassword]].map(([label,value,setter]) => <label key={label as string} className="block text-sm text-ink-700">{label as string}<input type="password" required minLength={label === c.current ? 1 : 8} maxLength={128} value={value as string} onChange={(e) => (setter as (v:string)=>void)(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>)}
      <button disabled={busy !== null} className="rounded-lg bg-ink-900 px-5 py-2.5 font-medium text-white disabled:opacity-60">{busy === "password" ? c.changing : c.change}</button>
    </form>
  </div></main>;
}
