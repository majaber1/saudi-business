"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { clearToken, getToken, me } from "@/lib/api";

export function AppTopBar({ onMobileMenuToggle }: { onMobileMenuToggle: () => void }) {
  const { locale, toggle } = useLanguage();
  const ar = locale === "ar";
  const [signedIn, setSignedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function refreshAuth() {
      const token = getToken();
      if (!token) return setSignedIn(false);
      try {
        await me(token);
        setSignedIn(true);
      } catch {
        clearToken();
        setSignedIn(false);
      }
    }
    void refreshAuth();
    window.addEventListener("sb-auth-change", refreshAuth);
    return () => window.removeEventListener("sb-auth-change", refreshAuth);
  }, []);

  return (
    <header
      className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur-md lg:px-6"
      data-testid="app-topbar"
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onMobileMenuToggle}
          className="grid h-9 w-9 place-items-center rounded-lg border border-slate-200 text-ink-600 lg:hidden"
          aria-label={ar ? "القائمة" : "Menu"}
          data-testid="mobile-menu-toggle"
        >
          ☰
        </button>
        <Link href="/" className="flex items-center gap-2 lg:hidden">
          <span className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 text-sm font-bold text-white">
            {ar ? "س" : "S"}
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggle}
          aria-label="Switch language"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-ink-600 transition-colors hover:border-brand-400 hover:text-brand-600"
        >
          {ar ? "EN" : "ع"}
        </button>
        {signedIn ? (
          <>
            <Link
              href="/settings"
              data-testid="topbar-settings"
              className="hidden rounded-lg px-3 py-1.5 text-sm font-medium text-ink-600 hover:text-brand-600 sm:inline-block"
            >
              {ar ? "حسابي" : "Account"}
            </Link>
            <button
              type="button"
              data-testid="topbar-logout"
              onClick={() => {
                clearToken();
                setSignedIn(false);
                window.dispatchEvent(new Event("sb-auth-change"));
                router.push("/login");
                router.refresh();
              }}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-ink-700 hover:border-brand-400 hover:text-brand-700"
            >
              {ar ? "خروج" : "Log out"}
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="rounded-lg px-3 py-1.5 text-sm font-medium text-ink-600 hover:text-brand-600">
              {ar ? "دخول" : "Log in"}
            </Link>
            <Link href="/register" className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-brand-700">
              {ar ? "إنشاء حساب" : "Sign up"}
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
