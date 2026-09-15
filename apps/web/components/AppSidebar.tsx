"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";

interface NavItem {
  href: string;
  icon: string;
  labelAr: string;
  labelEn: string;
  testId: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", icon: "⌘", labelAr: "مركز التحكم", labelEn: "Command Center", testId: "nav-command-center" },
  { href: "/businesses", icon: "◆", labelAr: "أعمالي", labelEn: "My Businesses", testId: "nav-my-businesses" },
  { href: "/businesses/new", icon: "+", labelAr: "عمل جديد", labelEn: "New Business", testId: "nav-new-business" },
  { href: "/tools/reports", icon: "▤", labelAr: "التقارير", labelEn: "Reports", testId: "nav-reports" },
  { href: "/settings", icon: "⚙", labelAr: "الإعدادات", labelEn: "Settings", testId: "nav-settings" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppSidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const pathname = usePathname() || "/";
  const { locale } = useLanguage();
  const ar = locale === "ar";

  return (
    <aside
      data-testid="app-sidebar"
      className={`fixed top-0 bottom-0 z-30 flex flex-col border-e border-slate-200/80 bg-white transition-[width] duration-200 ${
        collapsed ? "w-[68px]" : "w-[240px]"
      }`}
    >
      <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-slate-100 px-4">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 text-sm font-bold text-white shadow-card">
            {ar ? "س" : "S"}
          </span>
          {!collapsed && (
            <span className="text-base font-semibold tracking-tight text-ink-900">
              {ar ? "سعودي بزنس" : "Saudi Business"}
            </span>
          )}
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label={ar ? "التنقل الرئيسي" : "Main navigation"}>
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  data-testid={item.testId}
                  title={collapsed ? (ar ? item.labelAr : item.labelEn) : undefined}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-50 text-brand-700 font-semibold"
                      : "text-ink-600 hover:bg-slate-50 hover:text-ink-900"
                  }`}
                >
                  <span className={`grid h-6 w-6 shrink-0 place-items-center text-base ${active ? "text-brand-600" : "text-ink-500"}`}>
                    {item.icon}
                  </span>
                  {!collapsed && <span>{ar ? item.labelAr : item.labelEn}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-slate-100 px-3 py-3">
        <button
          onClick={onToggle}
          data-testid="sidebar-toggle"
          className="flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-ink-500 transition-colors hover:bg-slate-50 hover:text-ink-700"
          aria-label={collapsed ? (ar ? "توسيع القائمة" : "Expand sidebar") : (ar ? "طي القائمة" : "Collapse sidebar")}
        >
          <span className="text-base">{collapsed ? "»" : "«"}</span>
          {!collapsed && <span>{ar ? "طي القائمة" : "Collapse"}</span>}
        </button>
      </div>
    </aside>
  );
}

export function MobileSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname() || "/";
  const { locale } = useLanguage();
  const ar = locale === "ar";

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={onClose} data-testid="mobile-sidebar-overlay" />
      <aside
        data-testid="mobile-sidebar"
        className="fixed top-0 bottom-0 z-50 w-[280px] bg-white shadow-xl start-0"
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-100 px-4">
          <Link href="/" onClick={onClose} className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 text-sm font-bold text-white">
              {ar ? "س" : "S"}
            </span>
            <span className="text-base font-semibold text-ink-900">{ar ? "سعودي بزنس" : "Saudi Business"}</span>
          </Link>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-ink-500 hover:bg-slate-100" aria-label={ar ? "إغلاق" : "Close"}>
            ✕
          </button>
        </div>
        <nav className="px-3 py-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    data-testid={`mobile-${item.testId}`}
                    className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors ${
                      active
                        ? "bg-brand-50 text-brand-700 font-semibold"
                        : "text-ink-600 hover:bg-slate-50 hover:text-ink-900"
                    }`}
                  >
                    <span className={`grid h-6 w-6 place-items-center text-base ${active ? "text-brand-600" : "text-ink-500"}`}>
                      {item.icon}
                    </span>
                    <span>{ar ? item.labelAr : item.labelEn}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>
    </>
  );
}
