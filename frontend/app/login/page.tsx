"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err?.message || "ورود ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f5f1] p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-2xl font-bold text-white">
            ف
          </div>
          <h1 className="text-2xl font-bold">فرکس</h1>
          <p className="text-sm text-muted-foreground">پلتفرم طراحی پارامتریک آشپزخانه</p>
        </div>

        <div className="rounded-2xl border border-border bg-white p-8 shadow-sm">
          <form onSubmit={submit} className="space-y-4">
            <Field label="ایمیل">
              <Input
                type="email"
                dir="ltr"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.ir"
                required
              />
            </Field>
            <Field label="رمز عبور">
              <Input
                type="password"
                dir="ltr"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </Field>
            {error && (
              <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
            )}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "در حال ورود..." : "ورود"}
            </Button>
          </form>

          <div className="mt-4 rounded-lg bg-muted/50 px-3 py-2 text-center text-xs text-muted-foreground">
            کاربر نمایشی: demo@firx.ir / demo1234
          </div>

          <p className="mt-5 text-center text-sm text-muted-foreground">
            شرکت ندارید؟{" "}
            <Link href="/register" className="font-medium text-primary hover:underline">
              ساخت حساب جدید
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
