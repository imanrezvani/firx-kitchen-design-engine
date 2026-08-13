"use client";

import { useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import { faNumber } from "@/lib/format";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, Modal, EmptyState } from "@/components/ui/field";
import { Select } from "@/components/ui/input";

type Tab = "cabinets" | "materials" | "appliances";

interface Cabinet {
  id: string;
  code: string;
  name: string;
  cabinet_type: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  base_price: number;
  is_active: boolean;
}

interface Material {
  id: string;
  code: string;
  name: string;
  material_type: string;
  thickness_mm: number;
  color?: string | null;
  price_per_sqm: number;
}

interface Appliance {
  id: string;
  code: string;
  name: string;
  brand?: string | null;
  model?: string | null;
  appliance_type: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  price: number;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "cabinets", label: "کابینت‌ها" },
  { key: "materials", label: "متریال‌ها" },
  { key: "appliances", label: "لوازم" },
];

export default function CatalogPage() {
  const [tab, setTab] = useState<Tab>("cabinets");
  const [cabinets, setCabinets] = useState<Cabinet[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [appliances, setAppliances] = useState<Appliance[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<null | { mode: "create"; tab: Tab } | { mode: "edit"; tab: Tab; id: string }>(null);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [c, m, a] = await Promise.all([
        apiGet<Cabinet[]>("/api/v1/catalog/cabinets"),
        apiGet<Material[]>("/api/v1/catalog/materials"),
        apiGet<Appliance[]>("/api/v1/catalog/appliances"),
      ]);
      setCabinets(c);
      setMaterials(m);
      setAppliances(a);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function openCreate(t: Tab) {
    setModal({ mode: "create", tab: t });
  }

  function openEdit(t: Tab, id: string) {
    setModal({ mode: "edit", tab: t, id });
  }

  async function remove(t: Tab, id: string) {
    if (!confirm("آیا این آیتم حذف شود؟")) return;
    try {
      await apiDelete(`/api/v1/catalog/${t}/${id}`);
      load();
    } catch (err: any) {
      alert(err.message);
    }
  }

  function ModalForm({ onClose }: { onClose: () => void }) {
    const isCabinet = modal?.tab === "cabinets";
    const isMaterial = modal?.tab === "materials";
    const [f, setF] = useState<Record<string, any>>({});

    const editing = modal?.mode === "edit"
      ? (modal.tab === "cabinets" ? cabinets : modal.tab === "materials" ? materials : appliances).find((x) => x.id === modal.id)
      : null;

    async function save(e: React.FormEvent) {
      e.preventDefault();
      const body: Record<string, any> = { ...f };
      const url = `/api/v1/catalog/${modal!.tab}${editing ? `/${editing.id}` : ""}`;
      try {
        if (editing) await apiPut(url, body);
        else await apiPost(url, body);
        onClose();
        load();
      } catch (err: any) {
        alert(err.message);
      }
    }

    return (
      <form onSubmit={save} className="grid grid-cols-2 gap-4">
        <Field label="کد">
          <Input dir="ltr" value={f.code ?? ""} onChange={(e) => setF({ ...f, code: e.target.value })} required />
        </Field>        <Field label="نام">
          <Input value={f.name ?? ""} onChange={(e) => setF({ ...f, name: e.target.value })} required />
        </Field>
        <Field label="نوع">
          <Input value={f.cabinet_type ?? f.material_type ?? f.appliance_type ?? ""} onChange={(e) => setF({ ...f, [isCabinet ? "cabinet_type" : isMaterial ? "material_type" : "appliance_type"]: e.target.value })} required />
        </Field>
        {!isMaterial && (
          <Field label="برند">
            <Input value={f.brand ?? ""} onChange={(e) => setF({ ...f, brand: e.target.value })} />
          </Field>
        )}
        {isMaterial && (
          <Field label="ضخامت (mm)">
            <Input type="number" value={f.thickness_mm ?? ""} onChange={(e) => setF({ ...f, thickness_mm: +e.target.value })} required />
          </Field>
        )}
        {!isMaterial && (
          <Field label="عرض (mm)">
            <Input type="number" value={f.width_mm ?? ""} onChange={(e) => setF({ ...f, width_mm: +e.target.value })} required />
          </Field>
        )}
        {!isMaterial && (
          <Field label="ارتفاع (mm)">
            <Input type="number" value={f.height_mm ?? ""} onChange={(e) => setF({ ...f, height_mm: +e.target.value })} required />
          </Field>
        )}
        {!isMaterial && (
          <Field label="عمق (mm)">
            <Input type="number" value={f.depth_mm ?? ""} onChange={(e) => setF({ ...f, depth_mm: +e.target.value })} required />
          </Field>
        )}
        <Field label={isMaterial ? "قیمت هر متر مربع" : isCabinet ? "قیمت پایه" : "قیمت"}>
          <Input type="number" value={f.base_price ?? f.price_per_sqm ?? f.price ?? ""} onChange={(e) => setF({ ...f, [isMaterial ? "price_per_sqm" : isCabinet ? "base_price" : "price"]: +e.target.value })} />
        </Field>
        {isCabinet && (
          <Field label="فعال">
            <Select value={f.is_active === undefined ? "true" : String(f.is_active)} onChange={(e) => setF({ ...f, is_active: e.target.value === "true" })}>
              <option value="true">فعال</option>
              <option value="false">غیرفعال</option>
            </Select>
          </Field>
        )}
        <div className="col-span-2 flex justify-end gap-2 pt-2">
          <Button variant="outline" type="button" onClick={onClose}>انصراف</Button>
          <Button type="submit">{editing ? "ذخیره" : "ایجاد"}</Button>
        </div>
      </form>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">کاتالوگ محصولات</h1>
        <Button onClick={() => openCreate(tab)}>+ افزودن</Button>
      </div>

      <div className="flex gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${tab === t.key ? "bg-primary text-white" : "bg-muted/40 hover:bg-muted"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}

      {loading ? (
        <p className="text-muted-foreground">در حال بارگذاری...</p>
      ) : (
        <Card>
          <CardBody className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="px-5 py-3">کد</th>
                  <th className="px-5 py-3">نام</th>
                  <th className="px-5 py-3">ابعاد (عرض×ارتفاع×عمق)</th>
                  <th className="px-5 py-3">قیمت</th>
                  <th className="px-5 py-3 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {(tab === "cabinets" ? cabinets : tab === "materials" ? materials : appliances).map((item: any) => (
                  <tr key={item.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                    <td className="px-5 py-3 font-mono text-xs" dir="ltr">{item.code}</td>
                    <td className="px-5 py-3 font-medium">{item.name}</td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {item.width_mm ? `${faNumber(item.width_mm)}×${faNumber(item.height_mm)}×${faNumber(item.depth_mm)}` : `ضخامت ${faNumber(item.thickness_mm)}mm`}
                    </td>
                    <td className="px-5 py-3">
                      {faNumber(item.base_price ?? item.price_per_sqm ?? item.price)}
                      {tab === "materials" ? " تومان/م۲" : " تومان"}
                    </td>
                    <td className="px-5 py-3 text-left">
                      <div className="inline-flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => openEdit(tab, item.id)}>ویرایش</Button>
                        <Button variant="ghost" size="sm" className="text-danger" onClick={() => remove(tab, item.id)}>حذف</Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {tab === "cabinets" && !cabinets.length && <tr><td colSpan={5}><EmptyState title="کابینتی ثبت نشده" /></td></tr>}
                {tab === "materials" && !materials.length && <tr><td colSpan={5}><EmptyState title="متریالی ثبت نشده" /></td></tr>}
                {tab === "appliances" && !appliances.length && <tr><td colSpan={5}><EmptyState title="لوازمی ثبت نشده" /></td></tr>}
              </tbody>
            </table>
          </CardBody>
        </Card>
      )}

      <Modal open={!!modal} onClose={() => setModal(null)} title={modal?.mode === "edit" ? "ویرایش آیتم" : "آیتم جدید"}>
        {modal && <ModalForm onClose={() => setModal(null)} />}
      </Modal>
    </div>
  );
}
