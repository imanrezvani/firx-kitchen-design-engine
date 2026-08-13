"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    full_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("رمز عبور و تکرار آن یکسان نیستند");
      return;
    }
    setBusy(true);
    try {
      await register({
        company_name: form.company_name,
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      });
      router.push("/");
    } catch (err: any) {
      setError(err?.message || "ساخت حساب ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f5f1] p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold">ایجاد حساب سازمانی</h1>
          <p className="text-sm text-muted-foreground">شرکت و فضای کاری خود را بسازید</p>
        </div>
        <div className="rounded-2xl border border-border bg-white p-8 shadow-sm">
          <form onSubmit={submit} className="space-y-4">
            <Field label="نام شرکت">
              <Input value={form.company_name} onChange={set("company_name")} placeholder="شرکت دکوراسیون ..." required />
            </Field>
            <Field label="نام و نام خانوادگی">
              <Input value={form.full_name} onChange={set("full_name")} required />
            </Field>
            <Field label="ایمیل">
              <Input type="email" dir="ltr" value={form.email} onChange={set("email")} required />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="رمز عبور">
                <Input type="password" dir="ltr" value={form.password} onChange={set("password")} required />
              </Field>
              <Field label="تکرار رمز">
                <Input type="password" dir="ltr" value={form.confirm} onChange={set("confirm")} required />
              </Field>
            </div>
            {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "در حال ساخت..." : "ساخت حساب"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
