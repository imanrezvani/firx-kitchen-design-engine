"use client";

import { useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import { toJalali } from "@/lib/format";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, Modal, EmptyState } from "@/components/ui/field";

interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  email?: string | null;
  notes?: string | null;
  created_at: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<null | { mode: "create" } | { mode: "edit"; customer: Customer }>(null);
  const [form, setForm] = useState({ first_name: "", last_name: "", phone: "", email: "", notes: "" });
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      setCustomers(await apiGet<Customer[]>("/api/v1/customers"));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function openCreate() {
    setForm({ first_name: "", last_name: "", phone: "", email: "", notes: "" });
    setModal({ mode: "create" });
  }

  function openEdit(c: Customer) {
    setForm({
      first_name: c.first_name,
      last_name: c.last_name,
      phone: c.phone || "",
      email: c.email || "",
      notes: c.notes || "",
    });
    setModal({ mode: "edit", customer: c });
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const body = {
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone || null,
        email: form.email || null,
        notes: form.notes || null,
      };
      if (modal?.mode === "create") await apiPost("/api/v1/customers", body);
      else await apiPut(`/api/v1/customers/${modal!.customer.id}`, body);
      setModal(null);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function remove(c: Customer) {
    if (!confirm(`آیا مشتری «${c.first_name} ${c.last_name}» حذف شود؟`)) return;
    try {
      await apiDelete(`/api/v1/customers/${c.id}`);
      load();
    } catch (err: any) {
      alert(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">مشتریان</h1>
        <Button onClick={openCreate}>+ مشتری جدید</Button>
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}

      {loading ? (
        <p className="text-muted-foreground">در حال بارگذاری...</p>
      ) : !customers.length ? (
        <Card>
          <EmptyState title="مشتری‌ای ثبت نشده" description="اطلاعات مشتریان خود را اضافه کنید" />
        </Card>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {customers.map((c) => (
            <Card key={c.id}>
              <CardHeader>
                <CardTitle>
                  {c.first_name} {c.last_name}
                </CardTitle>
              </CardHeader>
              <CardBody className="space-y-2 text-sm">
                <p className="text-muted-foreground">{c.phone || "بدون تلفن"}</p>
                {c.email && <p className="text-muted-foreground" dir="ltr">{c.email}</p>}
                {c.notes && <p className="rounded-lg bg-muted/40 px-2 py-1 text-xs">{c.notes}</p>}
                <p className="text-xs text-muted-foreground">ایجاد: {toJalali(c.created_at)}</p>
                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" onClick={() => openEdit(c)}>ویرایش</Button>
                  <Button variant="ghost" size="sm" className="text-danger" onClick={() => remove(c)}>حذف</Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal?.mode === "edit" ? "ویرایش مشتری" : "مشتری جدید"}
        footer={
          <>
            <Button variant="outline" onClick={() => setModal(null)}>انصراف</Button>
            <Button type="submit" form="customer-form">{modal?.mode === "edit" ? "ذخیره" : "ایجاد"}</Button>
          </>
        }
      >
        <form id="customer-form" onSubmit={save} className="grid grid-cols-2 gap-4">
          <Field label="نام">
            <Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required />
          </Field>
          <Field label="نام خانوادگی">
            <Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required />
          </Field>
          <Field label="تلفن">
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="ایمیل">
            <Input type="email" dir="ltr" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <Field label="یادداشت" className="col-span-2">
            <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </Field>
        </form>
      </Modal>
    </div>
  );
}
