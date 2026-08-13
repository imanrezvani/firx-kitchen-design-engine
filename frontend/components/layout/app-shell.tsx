"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 right-0 z-30 flex w-64 flex-col border-l border-border bg-white">
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

      {/* Main */}
      <main className="mr-64 flex-1 p-6">{children}</main>
    </div>
  );
}
