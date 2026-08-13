"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import { toJalali, STATUS_FA } from "@/lib/format";
import { Card, CardBody, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, Modal, EmptyState } from "@/components/ui/field";
import { Select } from "@/components/ui/input";

interface Project {
  id: string;
  name: string;
  customer_id?: string | null;
  status: string;
  notes?: string | null;
  created_at: string;
}

interface Customer {
  id: string;
  first_name: string;
  last_name: string;
}

const STATUSES = ["draft", "designing", "needs_review", "approved", "completed", "archived"];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<null | { mode: "create" } | { mode: "edit"; project: Project }>(null);
  const [form, setForm] = useState({ name: "", customer_id: "", status: "draft", notes: "" });
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([
        apiGet<Project[]>("/api/v1/projects"),
        apiGet<Customer[]>("/api/v1/customers").catch(() => []),
      ]);
      setProjects(p);
      setCustomers(c);
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
    setForm({ name: "", customer_id: "", status: "draft", notes: "" });
    setModal({ mode: "create" });
  }

  function openEdit(p: Project) {
    setForm({ name: p.name, customer_id: p.customer_id || "", status: p.status, notes: p.notes || "" });
    setModal({ mode: "edit", project: p });
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const body = {
        name: form.name,
        customer_id: form.customer_id || null,
        status: form.status,
        notes: form.notes || null,
      };
      if (modal?.mode === "create") await apiPost("/api/v1/projects", body);
      else await apiPut(`/api/v1/projects/${modal!.project.id}`, body);
      setModal(null);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function remove(p: Project) {
    if (!confirm(`آیا پروژه «${p.name}» حذف شود؟`)) return;
    try {
      await apiDelete(`/api/v1/projects/${p.id}`);
      load();
    } catch (err: any) {
      alert(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">پروژه‌ها</h1>
        <Button onClick={openCreate}>+ پروژه جدید</Button>
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}

      {loading ? (
        <p className="text-muted-foreground">در حال بارگذاری...</p>
      ) : !projects.length ? (
        <Card>
          <EmptyState
            title="پروژه‌ای ثبت نشده"
            description="یک پروژه جدید ایجاد کنید یا وارد بخش طراحی شوید"
          />
        </Card>
      ) : (
        <Card>
          <CardBody className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="px-5 py-3">نام پروژه</th>
                  <th className="px-5 py-3">مشتری</th>
                  <th className="px-5 py-3">وضعیت</th>
                  <th className="px-5 py-3">تاریخ ایجاد</th>
                  <th className="px-5 py-3 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => {
                  const st = STATUS_FA[p.status] || STATUS_FA.draft;
                  const cust = customers.find((c) => c.id === p.customer_id);
                  return (
                    <tr key={p.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                      <td className="px-5 py-3">
                        <Link href={`/projects/${p.id}`} className="font-medium hover:text-primary">
                          {p.name}
                        </Link>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {cust ? `${cust.first_name} ${cust.last_name}` : "—"}
                      </td>
                      <td className="px-5 py-3">
                        <Badge color={st.color as any}>{st.label}</Badge>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{toJalali(p.created_at)}</td>
                      <td className="px-5 py-3 text-left">
                        <div className="inline-flex gap-2">
                          <Link href={`/designer?project=${p.id}`}>
                            <Button variant="outline" size="sm">طراحی</Button>
                          </Link>
                          <Button variant="outline" size="sm" onClick={() => openEdit(p)}>ویرایش</Button>
                          <Button variant="ghost" size="sm" className="text-danger" onClick={() => remove(p)}>حذف</Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardBody>
        </Card>
      )}

      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal?.mode === "edit" ? "ویرایش پروژه" : "پروژه جدید"}
        footer={
          <>
            <Button variant="outline" onClick={() => setModal(null)}>انصراف</Button>
            <Button type="submit" form="project-form">{modal?.mode === "edit" ? "ذخیره" : "ایجاد"}</Button>
          </>
        }
      >
        <form id="project-form" onSubmit={save} className="space-y-4">
          <Field label="نام پروژه">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </Field>
          <Field label="مشتری">
            <Select value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
              <option value="">بدون مشتری</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="وضعیت">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_FA[s]?.label || s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="توضیحات">
            <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </Field>
        </form>
      </Modal>
    </div>
  );
}
