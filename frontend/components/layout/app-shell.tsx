"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "داشبورد", icon: "▦" },
  { href: "/projects", label: "پروژه‌ها", icon: "▣" },
  { href: "/customers", label: "مشتریان", icon: "☺" },
  { href: "/designer", label: "طراحی آشپزخانه", icon: "✎" },
  { href: "/ai-designer", label: "طراحی هوشمند", icon: "✦" },
  { href: "/catalog", label: "کاتالوگ", icon: "◫" },
  { href: "/reports", label: "گزارش‌ها", icon: "▤" },
  { href: "/settings", label: "تنظیمات", icon: "⚙" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, tenant, logout, loading } = useAuth();
  const [navOpen, setNavOpen] = useState(false);
  const [dark, setDark] = useState(false);

  // Initialise theme: saved preference, else system preference.
  useEffect(() => {
    const saved = localStorage.getItem("firx_theme");
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    const isDark = saved ? saved === "dark" : !!prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  function toggleTheme() {
    setDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("firx_theme", next ? "dark" : "light");
      return next;
    });
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        در حال بارگذاری...
      </div>
    );
  }

  if (!user) {
    if (typeof window !== "undefined") window.location.href = "/login";
    return null;
  }

  function closeNav() {
    setNavOpen(false);
  }

  const sidebar = (
    <aside className="flex h-full w-64 flex-col border-l border-border bg-card">
      <div className="flex items-center gap-3 border-b border-border px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-lg text-white">
          ف
        </div>
        <div>
          <p className="text-sm font-bold">فرکس</p>
          <p className="text-xs text-muted-foreground">{tenant?.name || "طراحی آشپزخانه"}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeNav}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active ? "bg-primary/10 font-bold text-primary" : "text-foreground hover:bg-muted/40",
              )}
            >
              <span className="w-5 text-center text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <button
          onClick={toggleTheme}
          className="mb-3 flex w-full items-center justify-between rounded-lg border border-border px-3 py-2 text-xs hover:bg-muted/40"
        >
          <span>{dark ? "حالت روشن" : "حالت تاریک"}</span>
          <span>{dark ? "☀" : "☾"}</span>
        </button>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{user.full_name || user.email}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
          <button
            onClick={logout}
            className="rounded-md px-2 py-1 text-xs text-danger hover:bg-danger/10"
          >
            خروج
          </button>
        </div>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-card px-4 lg:hidden">
        <button
          onClick={() => setNavOpen(true)}
          aria-label="باز کردن منو"
          className="rounded-lg border border-border px-3 py-1.5 text-sm"
        >
          ☰
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-sm text-white">
            ف
          </div>
          <span className="text-sm font-bold">فرکس</span>
        </div>
        <button
          onClick={toggleTheme}
          aria-label="تغییر پوسته"
          className="rounded-lg border border-border px-3 py-1.5 text-sm"
        >
          {dark ? "☀" : "☾"}
        </button>
      </header>

      {/* Mobile drawer */}
      {navOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={closeNav} />
          <div className="absolute inset-y-0 right-0 w-64 shadow-xl">{sidebar}</div>
        </div>
      )}

      {/* Desktop sidebar (hidden on < lg) */}
      <div className="fixed inset-y-0 right-0 z-30 hidden lg:block">{sidebar}</div>

      {/* Main */}
      <main className="lg:mr-64 px-4 py-5 sm:px-6">{children}</main>
    </div>
  );
}
