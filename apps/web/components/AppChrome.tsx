"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Footer } from "@/components/Footer";
import { AppSidebar, MobileSidebar } from "@/components/AppSidebar";
import { useLanguage } from "@/components/LanguageProvider";
import { AppTopBar } from "@/components/AppTopBar";
import { Navbar } from "@/components/Navbar";

const MARKETING_PREFIXES = [
  "/pricing",
  "/help",
  "/about",
  "/opportunities",
  "/franchises",
  "/ideas",
  "/multazim",
  "/funding",
];

const AUTH_GATE_PREFIXES = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
];

function isExactOrChild(pathname: string, prefix: string): boolean {
  if (prefix === "/") return pathname === "/";
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

function useShellMode(pathname: string | null): "marketing" | "auth" | "app" {
  const path = pathname || "/";
  if (AUTH_GATE_PREFIXES.some((p) => isExactOrChild(path, p))) return "auth";
  if (MARKETING_PREFIXES.some((p) => isExactOrChild(path, p))) return "marketing";
  return "app";
}

function CompactProductFooter() {
  const { t, locale } = useLanguage();
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-slate-200 bg-white" data-testid="product-footer">
      <div className="flex flex-wrap items-center justify-between gap-2 px-6 py-3 text-xs text-ink-500">
        <p>
          © {year} {t.brand}
        </p>
        <p className="text-ink-400">
          {locale === "ar" ? "نظام أعمال ذكي" : "AI Business OS"}
        </p>
      </div>
    </footer>
  );
}

function AuthMinimalFooter() {
  const { t } = useLanguage();
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-slate-200 bg-white" data-testid="auth-footer">
      <div className="container-page py-3 text-center text-xs text-ink-500">
        © {year} {t.brand}
      </div>
    </footer>
  );
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const mode = useShellMode(pathname);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (mode === "app") {
    return (
      <div className="app-shell flex min-h-screen bg-[var(--sb-surface)]" data-shell="app" data-testid="app-chrome">
        <div className="hidden lg:block">
          <AppSidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        </div>
        <MobileSidebar open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
        <div
          className={`flex min-h-screen flex-1 flex-col transition-[margin] duration-200 ${
            sidebarCollapsed ? "lg:ms-[68px]" : "lg:ms-[240px]"
          }`}
        >
          <AppTopBar onMobileMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)} />
          <main className="flex-1 pb-4">{children}</main>
          <CompactProductFooter />
        </div>
      </div>
    );
  }

  if (mode === "auth") {
    return (
      <div className="auth-shell flex min-h-screen flex-col bg-slate-50" data-shell="auth" data-testid="app-chrome">
        <Navbar dense={false} />
        <main className="flex-1">{children}</main>
        <AuthMinimalFooter />
      </div>
    );
  }

  return (
    <div className="marketing-shell flex min-h-screen flex-col" data-shell="marketing" data-testid="app-chrome">
      <Navbar dense={false} />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
