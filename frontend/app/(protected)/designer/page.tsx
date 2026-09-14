"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiGet, apiPost, apiPut, getToken } from "@/lib/api";
import { faNumber, LAYOUT_FA } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { Card, CardBody, CardHeader, CardTitle, Badge } from "@/components/ui/card";
import { DesignCanvas } from "@/components/designer/design-canvas";

interface Project {
  id: string;
  name: string;
  status: string;
  customer_id?: string | null;
}

interface Room {
  id: string;
  project_id: string;
  name: string;
  width_mm: number;
  length_mm: number;
  height_mm: number;
  notes?: string | null;
  walls: any[];
  openings: any[];
  obstacles: any[];
}

interface Material {
  id: string;
  name: string;
  price_per_sqm: number;
}

interface DesignModel {
  id: string;
  name: string;
  layout: string;
  room: { width_mm: number; length_mm: number; height_mm: number; openings: any[] };
  cabinets: any[];
  appliances: any[];
  countertops: any[];
  clearances: any[];
  warnings: string[];
  score: number;
}

const LAYOUTS = ["linear", "L", "U", "galley", "island", "peninsula"];

const STEP_LABELS = ["انتخاب پروژه", "مشخصات فضا", "چیدمان و متریال", "طراحی و ویرایش"];

export default function DesignerPage() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [room, setRoom] = useState<Room | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [layout, setLayout] = useState("L");
  const [countertopId, setCountertopId] = useState("");
  const [cabinetMatId, setCabinetMatId] = useState("");
  const [design, setDesign] = useState<DesignModel | null>(null);
  const [selectedCabId, setSelectedCabId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [step, setStep] = useState(1);
  const [validation, setValidation] = useState<null | { score: number; results: { level: string; message: string }[] }>(null);
  const [bom, setBom] = useState<null | { rows: any[]; totals: any; sheets: any; parts?: any[] }>(null);
  const [drawings, setDrawings] = useState<null | { plan: any; elevations: any[] }>(null);
  const [cost, setCost] = useState<null | { summary: any; subtotals: any; items: any; markup: any }>(null);
  const [cutList, setCutList] = useState<null | { parts: any[]; part_count: number; total_qty: number; sheets: any }>(null);
  const [viz, setViz] = useState<null | { prompt: string; cabinets: any[]; appliances: any[]; layout: string; note: string }>(null);
  const [priceCfg, setPriceCfg] = useState<null | Record<string, number>>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [verDesc, setVerDesc] = useState("");

  // room form state
  const [rf, setRf] = useState({ name: "آشپزخانه", width_mm: 4200, length_mm: 3600, height_mm: 2800, notes: "" });
  const [openings, setOpenings] = useState<any[]>([]);
  const [obstacles, setObstacles] = useState<any[]>([]);
  const [openForm, setOpenForm] = useState<null | "door" | "window">(null);
  const [oForm, setOForm] = useState<{ kind?: string; wall: string; position_mm: number; width_mm: number; height_mm: number; sill_height_mm: number }>({ wall: "north", position_mm: 200, width_mm: 900, height_mm: 2100, sill_height_mm: 0 });
  const [obForm, setObForm] = useState({ kind: "column", wall: "north", position_mm: 0, width_mm: 300, depth_mm: 200, height_mm: 2400, notes: "" });

  const preDesign = searchParams.get("design");
  const preProject = searchParams.get("project");
  const handledRef = useRef<{ design?: boolean; project?: boolean }>({});
  const editTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function load() {
    try {
      const [ps, ms] = await Promise.all([
        apiGet<Project[]>("/api/v1/projects"),
        apiGet<Material[]>("/api/v1/catalog/materials"),
      ]);
      setProjects(ps);
      setMaterials(ms);
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (preDesign && !handledRef.current.design) {
      handledRef.current.design = true;
      openExisting(preDesign);
    }
  }, [preDesign]);

  useEffect(() => {
    if (preProject && !handledRef.current.project) {
      handledRef.current.project = true;
      setProjectId(preProject);
    }
  }, [preProject]);

  async function openExisting(designId: string) {
    try {
      const d = await apiGet<DesignModel>(`/api/v1/designs/${designId}`);
      setDesign(d);
      setStep(4);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function selectProject() {
    if (!projectId) {
      setError("یک پروژه انتخاب کنید");
      return;
    }
    setError("");
    try {
      const r = await apiGet<Room | null>(`/api/v1/projects/${projectId}/room`);
      if (r) {
        setRoom(r);
        setRf({ name: r.name, width_mm: r.width_mm, length_mm: r.length_mm, height_mm: r.height_mm, notes: r.notes || "" });
        setOpenings(r.openings.map((o) => ({ ...o })));
        setObstacles(r.obstacles.map((o) => ({ ...o })));
      } else {
        setRoom(null);
        setRf({ name: "آشپزخانه", width_mm: 4200, length_mm: 3600, height_mm: 2800, notes: "" });
        setOpenings([]);
        setObstacles([]);
      }
      setStep(2);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function saveRoomAndContinue() {
    setError("");
    setLoading(true);
    try {
      const body = {
        project_id: projectId,
        name: rf.name,
        width_mm: Number(rf.width_mm),
        length_mm: Number(rf.length_mm),
        height_mm: Number(rf.height_mm),
        notes: rf.notes || null,
        walls: [
          { side: "north", length_mm: Number(rf.width_mm), thickness_mm: 150 },
          { side: "south", length_mm: Number(rf.width_mm), thickness_mm: 150 },
          { side: "east", length_mm: Number(rf.length_mm), thickness_mm: 150 },
          { side: "west", length_mm: Number(rf.length_mm), thickness_mm: 150 },
        ],
        openings: openings.map((o) => ({
          kind: o.kind,
          wall: o.wall,
          position_mm: o.position_mm,
          width_mm: o.width_mm,
          height_mm: o.height_mm,
          sill_height_mm: o.sill_height_mm || 0,
          swing: o.swing || null,
        })),
        obstacles: obstacles.map((o) => ({
          kind: o.kind,
          wall: o.wall || null,
          position_mm: o.position_mm || 0,
          width_mm: o.width_mm || 0,
          depth_mm: o.depth_mm || 0,
          height_mm: o.height_mm || 0,
          notes: o.notes || null,
        })),
      };
      const r = await apiPost<Room>(`/api/v1/projects/${projectId}/room`, body);
      setRoom(r);
      setStep(3);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function generate() {
    setError("");
    setLoading(true);
    setValidation(null);
    setBom(null);
    setVersions([]);
    try {
      const d = await apiPost<DesignModel>(`/api/v1/projects/${projectId}/designs/generate`, {
        room_id: room!.id,
        layout,
        countertop_material_id: countertopId || null,
        cabinet_material_id: cabinetMatId || null,
      });
      setDesign(d);
      setStep(4);
      setNotice("طرح با موفقیت تولید شد. می‌توانید کابینت‌ها را جابجا کنید و دوباره اعتبارسنجی کنید.");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const designRef = useRef<any>(null);
  designRef.current = design;

  async function editCabinets(cabs: any[]) {
    if (!designRef.current) return;
    const next = { ...designRef.current, cabinets: cabs };
    setDesign(next);
    setValidation(null);
    // optimistic local update now; persist debounced so rapid drags batch
    if (editTimerRef.current) clearTimeout(editTimerRef.current);
    const designId = designRef.current.id;
    const appliances = designRef.current.appliances;
    editTimerRef.current = setTimeout(async () => {
      try {
        const saved = await apiPut<DesignModel>(`/api/v1/designs/${designId}`, { cabinets: cabs, appliances });
        setDesign(saved);
      } catch (e: any) {
        setError(e.message);
      }
    }, 400);
  }

  const handleCanvasSelect = useCallback((id: string) => {
    setSelectedCabId(id);
  }, []);

  const handleCanvasEdit = useCallback((cab: any) => {
    const d = designRef.current;
    if (!d) return;
    const next = { ...d, cabinets: d.cabinets.map((c: any) => (c.id === cab.id ? cab : c)) };
    setDesign(next);
    setValidation(null);
    if (editTimerRef.current) clearTimeout(editTimerRef.current);
    const designId = d.id;
    const appliances = d.appliances;
    editTimerRef.current = setTimeout(async () => {
      try {
        const saved = await apiPut<DesignModel>(`/api/v1/designs/${designId}`, { cabinets: next.cabinets, appliances });
        setDesign(saved);
      } catch (e: any) {
        setError(e.message);
      }
    }, 400);
  }, []);

  async function validate() {
    if (!design) return;
    setError("");
    try {
      setValidation(await apiGet(`/api/v1/designs/${design.id}/validate`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadBom() {
    if (!design) return;
    setError("");
    try {
      setBom(await apiGet(`/api/v1/designs/${design.id}/bom`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadDrawings() {
    if (!design) return;
    setError("");
    try {
      setDrawings(await apiGet(`/api/v1/designs/${design.id}/drawings`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadCost() {
    if (!design) return;
    setError("");
    try {
      setCost(await apiGet(`/api/v1/designs/${design.id}/cost`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadCutList() {
    if (!design) return;
    setError("");
    try {
      setCutList(await apiGet(`/api/v1/designs/${design.id}/cut-list`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadVisualization() {
    if (!design) return;
    setError("");
    try {
      setViz(await apiGet(`/api/v1/designs/${design.id}/visualization`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadPriceCfg() {
    if (!projectId) return;
    setError("");
    try {
      const r = await apiGet<{ costing_config: Record<string, number> }>(`/api/v1/projects/${projectId}/costing`);
      setPriceCfg(r.costing_config);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function savePriceCfg() {
    if (!projectId || !priceCfg) return;
    setError("");
    try {
      const { margin_pct, overhead_pct, contingency_pct, material_tax_pct, delivery_fee } = priceCfg;
      await apiPut(`/api/v1/projects/${projectId}/costing`, {
        costing_config: { margin_pct, overhead_pct, contingency_pct, material_tax_pct, delivery_fee },
      });
      setNotice("تنظیمات قیمت‌گذاری ذخیره شد.");
      loadCost();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadVersions() {
    if (!design) return;
    try {
      setVersions(await apiGet(`/api/v1/designs/${design.id}/versions`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function saveVersion() {
    if (!design) return;
    try {
      await apiPost(`/api/v1/designs/${design.id}/versions`, { change_desc: verDesc || null });
      setVerDesc("");
      loadVersions();
      setNotice("نسخه جدید ذخیره شد.");
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function restoreVersion(vno: number) {
    if (!design) return;
    try {
      const d = await apiPost<DesignModel>(`/api/v1/designs/${design.id}/restore/${vno}`, {});
      setDesign(d);
      setValidation(null);
      setNotice(`نسخه ${faNumber(vno)} بازیابی شد.`);
    } catch (e: any) {
      setError(e.message);
    }
  }

  function addOpening() {
    if (!openForm) return;
    setOpenings((arr) => [...arr, { id: Math.random().toString(36).slice(2), ...oForm }]);
    setOpenForm(null);
  }

  function addObstacle() {
    setObstacles((arr) => [...arr, { id: Math.random().toString(36).slice(2), ...obForm }]);
    setObForm({ kind: "column", wall: "north", position_mm: 0, width_mm: 300, depth_mm: 200, height_mm: 2400, notes: "" });
  }

  const cabinetCount = design?.cabinets.length ?? 0;
  const wallCount = design?.cabinets.filter((c) => c.type === "wall").length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">طراحی آشپزخانه</h1>
        {design && <Badge color="green">امتیاز طرح: {faNumber(design.score)}</Badge>}
      </div>

      {/* Stepper */}
      <ol className="flex items-center gap-2 overflow-x-auto text-sm sm:gap-3">
        {STEP_LABELS.map((label, i) => {
          const n = i + 1;
          const done = step > n;
          return (
            <li key={label} className="flex shrink-0 items-center gap-2">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                  done ? "bg-success text-white" : step === n ? "bg-primary text-white" : "bg-muted/60 text-muted-foreground"
                }`}
              >
                {done ? "✓" : faNumber(n)}
              </span>
              <span className={`whitespace-nowrap max-sm:hidden ${step === n ? "font-bold" : "text-muted-foreground"}`}>{label}</span>
              {n < STEP_LABELS.length && <span className="mx-1 text-muted-foreground max-sm:hidden">—</span>}
            </li>
          );
        })}
      </ol>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}
      {notice && <p className="rounded-lg bg-success/10 px-3 py-2 text-sm text-success">{notice}</p>}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>انتخاب پروژه</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <Field label="پروژه" hint="برای یک پروژه جدید ابتدا از بخش پروژه‌ها آن را بسازید">
              <Select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                <option value="">انتخاب کنید...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Button onClick={selectProject}>ادامه: مشخصات فضا</Button>
          </CardBody>
        </Card>
      )}

      {step === 2 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>ابعاد فضا</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Field label="عرض (mm)">
                  <Input type="number" value={rf.width_mm} onChange={(e) => setRf({ ...rf, width_mm: +e.target.value })} />
                </Field>
                <Field label="طول (mm)">
                  <Input type="number" value={rf.length_mm} onChange={(e) => setRf({ ...rf, length_mm: +e.target.value })} />
                </Field>
                <Field label="ارتفاع (mm)">
                  <Input type="number" value={rf.height_mm} onChange={(e) => setRf({ ...rf, height_mm: +e.target.value })} />
                </Field>
                <Field label="نام فضا">
                  <Input value={rf.name} onChange={(e) => setRf({ ...rf, name: e.target.value })} />
                </Field>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <Field label="پنجره / درب (ارتفاع عتبه را برای پنجره وارد کنید)">
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" type="button" onClick={() => { setOForm({ ...oForm, kind: "window", sill_height_mm: 900 }); setOpenForm("window"); }}>+ پنجره</Button>
                    <Button variant="outline" size="sm" type="button" onClick={() => { setOForm({ ...oForm, kind: "door", sill_height_mm: 0 }); setOpenForm("door"); }}>+ درب</Button>
                  </div>
                </Field>
                <Field label="مانع (ستون، رادیاتور...)">
                  <Button variant="outline" size="sm" type="button" onClick={addObstacle}>+ مانع</Button>
                </Field>
              </div>

              {openForm && (
                <div className="mt-4 rounded-xl border border-border bg-muted/20 p-4">
                  <p className="mb-3 text-sm font-bold">{openForm === "window" ? "افزودن پنجره" : "افزودن درب"}</p>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    <Field label="دیوار">
                      <Select value={oForm.wall} onChange={(e) => setOForm({ ...oForm, wall: e.target.value })}>
                        <option value="north">شمال</option>
                        <option value="south">جنوب</option>
                        <option value="east">شرق</option>
                        <option value="west">غرب</option>
                      </Select>
                    </Field>
                    <Field label="فاصله از گوشه (mm)">
                      <Input type="number" value={oForm.position_mm} onChange={(e) => setOForm({ ...oForm, position_mm: +e.target.value })} />
                    </Field>
                    <Field label="عرض (mm)">
                      <Input type="number" value={oForm.width_mm} onChange={(e) => setOForm({ ...oForm, width_mm: +e.target.value })} />
                    </Field>
                    <Field label="ارتفاع (mm)">
                      <Input type="number" value={oForm.height_mm} onChange={(e) => setOForm({ ...oForm, height_mm: +e.target.value })} />
                    </Field>
                    {openForm === "window" && (
                      <Field label="ارتفاع عتبه (mm)">
                        <Input type="number" value={oForm.sill_height_mm} onChange={(e) => setOForm({ ...oForm, sill_height_mm: +e.target.value })} />
                      </Field>
                    )}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Button size="sm" onClick={addOpening}>افزودن</Button>
                    <Button variant="ghost" size="sm" onClick={() => setOpenForm(null)}>انصراف</Button>
                  </div>
                </div>
              )}

              {openings.length > 0 && (
                <div className="mt-4">
                  <p className="mb-2 text-sm font-bold">بازشوهای ثبت‌شده</p>
                  <div className="flex flex-wrap gap-2">
                    {openings.map((o) => (
                      <span key={o.id} className="inline-flex items-center gap-2 rounded-full bg-muted/40 px-3 py-1 text-xs">
                        {o.kind === "window" ? "پنجره" : "درب"} · {o.wall} · {faNumber(o.width_mm)}mm
                        <button className="text-danger" onClick={() => setOpenings((arr) => arr.filter((x) => x.id !== o.id))}>×</button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {obstacles.length > 0 && (
                <div className="mt-4">
                  <p className="mb-2 text-sm font-bold">موانع ثبت‌شده</p>
                  <div className="flex flex-wrap gap-2">
                    {obstacles.map((o) => (
                      <span key={o.id} className="inline-flex items-center gap-2 rounded-full bg-muted/40 px-3 py-1 text-xs">
                        مانع · {o.kind} · {o.wall || "بدون دیوار"}
                        <button className="text-danger" onClick={() => setObstacles((arr) => arr.filter((x) => x.id !== o.id))}>×</button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>راهنما</CardTitle>
            </CardHeader>
            <CardBody className="space-y-3 text-sm text-muted-foreground">
              <p>ابعاد فضای آشپزخانه را به میلی‌متر وارد کنید. سینک به‌صورت خودکار زیر پنجره قرار می‌گیرد.</p>
              <p>درب‌ها و پنجره‌ها در روند طراحی کابینت‌ها لحاظ می‌شوند.</p>
              <p>برای ثبت تغییرات و رفتن به مرحله بعد دکمه زیر را بزنید.</p>
              <Button className="mt-2 w-full" onClick={saveRoomAndContinue} disabled={loading}>
                {loading ? "در حال ذخیره..." : "ذخیره فضا و ادامه"}
              </Button>
            </CardBody>
          </Card>
        </div>
      )}

      {step === 3 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>انتخاب چیدمان</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-3 gap-3">
                {LAYOUTS.map((l) => (
                  <button
                    key={l}
                    onClick={() => setLayout(l)}
                    className={`rounded-xl border-2 p-4 text-center transition-colors ${
                      layout === l ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
                    }`}
                  >
                    <div className="mb-2 flex h-14 items-center justify-center">
                      <LayoutIcon layout={l} />
                    </div>
                    <p className="text-sm font-bold">{LAYOUT_FA[l]}</p>
                  </button>
                ))}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>متریال</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <Field label="صفحه کابینت (روی کانتر)">
                <Select value={countertopId} onChange={(e) => setCountertopId(e.target.value)}>
                  <option value="">پیش‌فرض (کورین)</option>
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </Select>
              </Field>
              <Field label="بدنه کابینت">
                <Select value={cabinetMatId} onChange={(e) => setCabinetMatId(e.target.value)}>
                  <option value="">پیش‌فرض</option>
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </Select>
              </Field>
              <p className="text-xs text-muted-foreground">
                فضای {faNumber(rf.width_mm)}×{faNumber(rf.length_mm)} میلی‌متر · چیدمان {LAYOUT_FA[layout]}
              </p>
              <Button className="w-full" onClick={generate} disabled={loading}>
                {loading ? "در حال تولید طرح..." : "تولید طرح"}
              </Button>
            </CardBody>
          </Card>
        </div>
      )}

      {step === 4 && design && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={validate}>اعتبارسنجی</Button>
            <Button variant="outline" size="sm" onClick={loadBom}>لیست متریال (BOM)</Button>
            <Button variant="outline" size="sm" onClick={loadCutList}>لیست برش</Button>
            <Button variant="outline" size="sm" onClick={loadCost}>قیمت‌گذاری</Button>
            <Button variant="outline" size="sm" onClick={async () => {
              if (!design) return;
              try {
                const res = await fetch(`/api/v1/designs/${design.id}/quote.html`, {
                  headers: { Authorization: `Bearer ${getToken()}` },
                });
                if (!res.ok) throw new Error("خطا در دریافت پیش‌فاکتور");
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                window.open(url, "_blank");
                setTimeout(() => URL.revokeObjectURL(url), 60000);
              } catch (e: any) {
                setError(e.message);
              }
            }}>پیش‌فاکتور (PDF/چاپ)</Button>
            <Button variant="outline" size="sm" onClick={loadVisualization}>پرامپت رندر AI</Button>
            <Button variant="outline" size="sm" onClick={loadDrawings}>نقشه‌های فنی</Button>
            <Button variant="outline" size="sm" onClick={loadVersions}>نسخه‌ها</Button>
            <Button variant="outline" size="sm" onClick={() => { setStep(3); }}>تولید مجدد</Button>
          </div>

          <DesignCanvas
            design={design}
            selectedId={selectedCabId}
            onSelect={handleCanvasSelect}
            onEdit={handleCanvasEdit}
          />

          {selectedCabId && (
            <CabinetProperties
              cabinet={design.cabinets.find((c: any) => c.id === selectedCabId) as any}
              materials={materials}
              onSave={(patch) => {
                const next = design.cabinets.map((c: any) =>
                  c.id === selectedCabId ? { ...c, ...patch } : c
                );
                editCabinets(next);
              }}
              onClose={() => setSelectedCabId(null)}
            />
          )}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle>مشخصات طرح</CardTitle>
              </CardHeader>
              <CardBody className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">چیدمان</span><span>{LAYOUT_FA[design.layout]}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">کابینت‌های زمینی</span><span>{faNumber(cabinetCount - wallCount)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">کابینت‌های دیواری</span><span>{faNumber(wallCount)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">لوازم</span><span>{faNumber(design.appliances.length)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">امتیاز</span><span className="font-bold text-success">{faNumber(design.score)}</span></div>
              </CardBody>
            </Card>

            {validation && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>نتایج اعتبارسنجی — امتیاز {faNumber(validation.score)}</CardTitle>
                </CardHeader>
                <CardBody className="max-h-64 space-y-2 overflow-y-auto">
                  {validation.results.map((r, i) => (
                    <div key={i} className={`flex items-start gap-2 rounded-lg px-3 py-2 text-sm ${
                      r.level === "error" ? "bg-danger/10 text-danger" : r.level === "warning" ? "bg-warning/10 text-warning" : "bg-success/10 text-success"
                    }`}>
                      <span className="font-bold">{r.level === "error" ? "✕" : r.level === "warning" ? "!" : "✓"}</span>
                      <span>{r.message}</span>
                    </div>
                  ))}
                  {!validation.results.length && <p className="text-sm text-success">هیچ موردی یافت نشد — طرح سالم است.</p>}
                </CardBody>
              </Card>
            )}

            {bom && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>لیست متریال (BOM)</CardTitle>
                </CardHeader>
                <CardBody className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-right text-xs text-muted-foreground">
                        <th className="px-5 py-2">نام</th>
                        <th className="px-5 py-2">دسته</th>
                        <th className="px-5 py-2">ابعاد</th>
                        <th className="px-5 py-2">قیمت واحد</th>
                        <th className="px-5 py-2">جمع</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bom.rows.map((r, i) => (
                        <tr key={i} className="border-b border-border/40 last:border-0">
                          <td className="px-5 py-2">{r.name}</td>
                          <td className="px-5 py-2 text-muted-foreground">
                            {r.category === "cabinet" ? "کابینت" : r.category === "appliance" ? "لوازم" : r.category === "hardware" ? "یراقآلات" : "صفحه"}
                          </td>
                          <td className="px-5 py-2 text-muted-foreground">{faNumber(r.width_mm)}×{faNumber(r.height_mm)}×{faNumber(r.depth_mm)}</td>
                          <td className="px-5 py-2">{faNumber(r.unit_price)} تومان</td>
                          <td className="px-5 py-2 font-medium">{faNumber(r.total_price)} تومان</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="flex flex-wrap justify-end gap-6 border-t border-border bg-muted/20 px-5 py-4 text-sm">
                    <span>کابینت: <b>{faNumber(bom.totals.cabinets)}</b></span>
                    <span>لوازم: <b>{faNumber(bom.totals.appliances)}</b></span>
                    <span>یراقآلات: <b>{faNumber(bom.totals.hardware)}</b></span>
                    <span>جمع کل: <b>{faNumber(bom.totals.grand_total)} تومان</b> ({bom.totals.accuracy})</span>
                    <span>ورق ۱۸ میلی‌متر: <b>{faNumber(bom.sheets.sheets_by_thickness?.[18] ?? 0)}</b></span>
                    <span>ورق ۱۶ میلی‌متر: <b>{faNumber(bom.sheets.sheets_by_thickness?.[16] ?? 0)}</b></span>
                    <span>متریال: <b>{faNumber(bom.sheets.total_m2)}</b> m²</span>
                  </div>
                  {bom.parts && bom.parts.length > 0 && (
                    <div className="max-h-64 overflow-auto border-t border-border">
                      <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/20">
                          <tr className="border-b border-border text-right text-xs text-muted-foreground">
                            <th className="px-5 py-2">کابینت</th>
                            <th className="px-5 py-2">قطعه</th>
                            <th className="px-5 py-2">ابعاد</th>
                            <th className="px-5 py-2">ضخامت</th>
                            <th className="px-5 py-2">تعداد</th>
                            <th className="px-5 py-2">لب‌چسب</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bom.parts.map((p, i) => (
                            <tr key={i} className="border-b border-border/40 last:border-0">
                              <td className="px-5 py-1">{p.cabinet}</td>
                              <td className="px-5 py-1">{p.part}</td>
                              <td className="px-5 py-1 text-muted-foreground">
                                {faNumber(p.width_mm)}×{faNumber(p.length_mm)}
                              </td>
                              <td className="px-5 py-1">{faNumber(p.thickness_mm)}</td>
                              <td className="px-5 py-1">{faNumber(p.qty)}</td>
                              <td className="px-5 py-1 text-muted-foreground">
                                {p.edge_banding?.join(" + ") || "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardBody>
              </Card>
            )}

            {cost && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>قیمت‌گذاری پروژه (مشتق از مدل)</CardTitle>
                </CardHeader>
                <CardBody className="space-y-3 text-sm">
                  <div className="flex flex-wrap items-center justify-between rounded-lg bg-muted/20 p-4">
                    <div>
                      <div className="text-xs text-muted-foreground">قیمت نهایی مصرف‌کننده</div>
                      <div className="text-2xl font-bold text-success">{faNumber(cost.summary.total_retail)} تومان</div>
                    </div>
                    <div className="text-left">
                      <div className="text-xs text-muted-foreground">قیمت به‌ازای هر متر خطی</div>
                      <div className="font-bold">{faNumber(cost.summary.price_per_linear_m)} تومان</div>
                    </div>
                  </div>
                  <table className="w-full text-sm">
                    <tbody>
                      <tr className="border-b border-border/40"><td className="py-1.5">متریال</td><td className="text-left">{faNumber(cost.subtotals.materials)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">یراق‌آلات</td><td className="text-left">{faNumber(cost.subtotals.hardware)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">لب‌چسب</td><td className="text-left">{faNumber(cost.subtotals.edge_banding)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">اکسسوری</td><td className="text-left">{faNumber(cost.subtotals.accessories)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">نیروی کار</td><td className="text-left">{faNumber(cost.subtotals.labor)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">لوازم</td><td className="text-left">{faNumber(cost.subtotals.appliances)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">صفحه کابینت</td><td className="text-left">{faNumber(cost.subtotals.countertops)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">هزینه‌های سربار</td><td className="text-left">{faNumber(cost.markup.overhead)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">سود</td><td className="text-left">{faNumber(cost.markup.margin_amount)}</td></tr>
                      <tr className="border-b border-border/40"><td className="py-1.5">مالیات</td><td className="text-left">{faNumber(cost.markup.tax)}</td></tr>
                      <tr><td className="py-1.5">هزینه ارسال</td><td className="text-left">{faNumber(cost.markup.delivery_fee)}</td></tr>
                    </tbody>
                  </table>
                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={loadPriceCfg}>تنظیمات قیمت</Button>
                      {priceCfg && (
                        <>
                          <div className="flex items-center gap-1 text-xs">
                            <span className="text-muted-foreground">سود %</span>
                            <input type="number" className="w-14 rounded border border-border bg-background px-1 py-0.5 text-left"
                              value={priceCfg.margin_pct ?? 0}
                              onChange={(e) => setPriceCfg({ ...priceCfg, margin_pct: Number(e.target.value) })} />
                          </div>
                          <div className="flex items-center gap-1 text-xs">
                            <span className="text-muted-foreground">سربار %</span>
                            <input type="number" className="w-14 rounded border border-border bg-background px-1 py-0.5 text-left"
                              value={priceCfg.overhead_pct ?? 0}
                              onChange={(e) => setPriceCfg({ ...priceCfg, overhead_pct: Number(e.target.value) })} />
                          </div>
                          <div className="flex items-center gap-1 text-xs">
                            <span className="text-muted-foreground">مالیات %</span>
                            <input type="number" className="w-14 rounded border border-border bg-background px-1 py-0.5 text-left"
                              value={priceCfg.material_tax_pct ?? 0}
                              onChange={(e) => setPriceCfg({ ...priceCfg, material_tax_pct: Number(e.target.value) })} />
                          </div>
                          <Button variant="outline" size="sm" onClick={savePriceCfg}>ذخیره</Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardBody>
              </Card>
            )}

            {viz && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>پرامپت رندر هوش مصنوعی (مشتق از مدل)</CardTitle>
                </CardHeader>
                <CardBody className="space-y-3">
                  <p className="rounded-lg bg-muted/20 p-3 text-sm leading-6 whitespace-pre-line" dir="rtl">{viz.prompt}</p>
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>کابینت: <b>{faNumber(viz.cabinets.length)}</b></span>
                    <span>لوازم: <b>{faNumber(viz.appliances.length)}</b></span>
                    <span>چیدمان: <b>{LAYOUT_FA[viz.layout] || viz.layout}</b></span>
                  </div>
                  <p className="text-xs text-muted-foreground">{viz.note}</p>
                </CardBody>
              </Card>
            )}

            {cutList && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>لیست برش (مشتق از مدل)</CardTitle>
                </CardHeader>
                <CardBody className="p-0">
                  <div className="flex flex-wrap gap-4 px-5 py-3 text-sm">
                    <span>قطعات: <b>{faNumber(cutList.part_count)}</b></span>
                    <span>جمع تعداد: <b>{faNumber(cutList.total_qty)}</b></span>
                    <span>ورق‌ها: <b>{faNumber(cutList.sheets.total_sheets)}</b> (۱۸mm: {faNumber(cutList.sheets.sheets_by_thickness?.[18] ?? 0)} · ۱۶mm: {faNumber(cutList.sheets.sheets_by_thickness?.[16] ?? 0)})</span>
                  </div>
                  <div className="max-h-72 overflow-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-muted/20">
                        <tr className="border-b border-border text-right text-xs text-muted-foreground">
                          <th className="px-5 py-2">شناسه</th>
                          <th className="px-5 py-2">کابینت</th>
                          <th className="px-5 py-2">قطعه</th>
                          <th className="px-5 py-2">ابعاد</th>
                          <th className="px-5 py-2">ضخامت</th>
                          <th className="px-5 py-2">تعداد</th>
                          <th className="px-5 py-2">جهت دانه</th>
                          <th className="px-5 py-2">لب‌چسب</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cutList.parts.map((p, i) => (
                          <tr key={i} className="border-b border-border/40 last:border-0">
                            <td className="px-5 py-1 font-medium" dir="ltr">{p.id}</td>
                            <td className="px-5 py-1">{p.cabinet}</td>
                            <td className="px-5 py-1">{p.part}</td>
                            <td className="px-5 py-1 text-muted-foreground">{faNumber(p.width_mm)}×{faNumber(p.length_mm)}</td>
                            <td className="px-5 py-1">{faNumber(p.thickness_mm)}</td>
                            <td className="px-5 py-1">{faNumber(p.qty)}</td>
                            <td className="px-5 py-1 text-muted-foreground">{({ vertical: "عمودی", horizontal: "افقی", any: "هر جهت" } as Record<string, string>)[p.grain] || p.grain}</td>
                            <td className="px-5 py-1 text-muted-foreground">{p.edge_banding?.join(" + ") || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardBody>
              </Card>
            )}

            {drawings && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>نقشه‌های فنی (مشتق از مدل)</CardTitle>
                </CardHeader>
                <CardBody className="space-y-4">
                  <div className="text-xs text-muted-foreground">
                    نقشه پلان: {faNumber(drawings.plan.cabinets.length)} کابینت ·
                    اتاق {faNumber(drawings.plan.room.width_mm)}×{faNumber(drawings.plan.room.length_mm)}
                  </div>
                  {drawings.elevations.map((s, i) => (
                    <div key={i}>
                      <div className="mb-1 text-sm font-medium">نما خط {s.wall}</div>
                      <div className="flex h-24 items-end gap-px overflow-x-auto rounded border border-border bg-muted/20 p-2">
                        {s.cabinets.map((c: any, j: number) => (
                          <div
                            key={j}
                            title={`${c.label} ${c.type} ${c.width_mm}×${c.height_mm} z=${c.z_mm}`}
                            className="flex shrink-0 flex-col items-center justify-end border border-border bg-background text-[9px] leading-tight"
                            style={{ width: Math.max(24, c.width_mm / 18), height: `${Math.max(18, Math.min(88, c.height_mm / 22))}%` }}
                          >
                            <span>{c.label}</span>
                            <span className="text-muted-foreground">{faNumber(c.width_mm)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </CardBody>
              </Card>
            )}

            {versions.length > 0 && (
              <Card className="md:col-span-3">
                <CardHeader>
                  <CardTitle>نسخه‌های طرح</CardTitle>
                </CardHeader>
                <CardBody className="space-y-3">
                  <div className="flex gap-2">
                    <Input placeholder="توضیح تغییر این نسخه..." value={verDesc} onChange={(e) => setVerDesc(e.target.value)} />
                    <Button variant="outline" size="sm" onClick={saveVersion}>ذخیره نسخه فعلی</Button>
                  </div>
                  <ul className="divide-y divide-border">
                    {versions.map((v) => (
                      <li key={v.id} className="flex items-center justify-between py-2">
                        <div>
                          <span className="font-bold">نسخه {faNumber(v.version_no)}</span>
                          <span className="mx-2 text-muted-foreground">{v.change_desc}</span>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => restoreVersion(v.version_no)}>بازیابی</Button>
                      </li>
                    ))}
                  </ul>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function CabinetProperties({
  cabinet,
  materials,
  onSave,
  onClose,
}: {
  cabinet: any;
  materials: any[];
  onSave: (patch: Record<string, any>) => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState<Record<string, any>>({
    name: cabinet.name ?? "",
    width_mm: cabinet.width_mm,
    height_mm: cabinet.height_mm,
    depth_mm: cabinet.depth_mm,
    door_config: cabinet.door_config ?? "",
    drawer_count: cabinet.drawer_count ?? "",
    shelf_count: cabinet.shelf_count ?? "",
    material_id: cabinet.material_id ?? "",
  });
  if (!cabinet) return null;

  const doorOptions = [
    ["", "پیش‌فرض (خودکار)"],
    ["none", "بدون درب"],
    ["single", "تک‌در"],
    ["double", "دودر"],
    ["lift_up", "درب بالارو"],
    ["split", "درب دولایه"],
    ["drawers_top", "کشو بالا + درب"],
  ];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>مشخصات کابینت {cabinet.name || ""}</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClose}>بستن</Button>
      </CardHeader>
      <CardBody className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <Field label="عرض (میلی‌متر)">
            <Input type="number" value={form.width_mm} onChange={(e) => setForm({ ...form, width_mm: Number(e.target.value) })} />
          </Field>
          <Field label="ارتفاع (میلی‌متر)">
            <Input type="number" value={form.height_mm} onChange={(e) => setForm({ ...form, height_mm: Number(e.target.value) })} />
          </Field>
          <Field label="عمق (میلی‌متر)">
            <Input type="number" value={form.depth_mm} onChange={(e) => setForm({ ...form, depth_mm: Number(e.target.value) })} />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="تنظیم درب">
            <Select value={form.door_config} onChange={(e) => setForm({ ...form, door_config: e.target.value })}>
              {doorOptions.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </Select>
          </Field>
          <Field label="تعداد کشو">
            <Input type="number" value={form.drawer_count} onChange={(e) => setForm({ ...form, drawer_count: e.target.value === "" ? null : Number(e.target.value) })} />
          </Field>
          <Field label="تعداد طبقه">
            <Input type="number" value={form.shelf_count} onChange={(e) => setForm({ ...form, shelf_count: e.target.value === "" ? null : Number(e.target.value) })} />
          </Field>
          <Field label="متریال بدنه">
            <Select value={form.material_id} onChange={(e) => setForm({ ...form, material_id: e.target.value })}>
              <option value="">پیش‌فرض</option>
              {materials.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </Select>
          </Field>
        </div>
        <Button className="w-full" onClick={() => {
          onSave({
            name: form.name,
            width_mm: form.width_mm,
            height_mm: form.height_mm,
            depth_mm: form.depth_mm,
            door_config: form.door_config || null,
            drawer_count: form.drawer_count,
            shelf_count: form.shelf_count,
            material_id: form.material_id || null,
          });
        }}>
          اعمال تغییرات
        </Button>
        <p className="text-xs text-muted-foreground">
          تغییر پارامترها، اجزای مشتق‌شده، سخت‌افزار، متریال، هزینه و نقشه‌ها را به‌صورت خودکار به‌روزرسانی می‌کند.
        </p>
      </CardBody>
    </Card>
  );
}

function LayoutIcon({ layout }: { layout: string }) {
  const stroke = "currentColor";
  return (
    <svg width="64" height="48" viewBox="0 0 64 48" fill="none" className="mx-auto text-primary">
      {layout === "linear" && <rect x="4" y="10" width="56" height="18" rx="2" stroke={stroke} strokeWidth="2" />}
      {layout === "L" && (
        <>
          <rect x="4" y="10" width="56" height="16" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="4" y="10" width="16" height="34" rx="2" stroke={stroke} strokeWidth="2" />
        </>
      )}
      {layout === "U" && (
        <>
          <rect x="4" y="10" width="16" height="34" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="44" y="10" width="16" height="34" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="4" y="10" width="56" height="16" rx="2" stroke={stroke} strokeWidth="2" />
        </>
      )}
      {layout === "galley" && (
        <>
          <rect x="4" y="6" width="16" height="36" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="44" y="6" width="16" height="36" rx="2" stroke={stroke} strokeWidth="2" />
        </>
      )}
      {layout === "island" && (
        <>
          <rect x="4" y="10" width="56" height="14" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="20" y="26" width="24" height="12" rx="2" stroke={stroke} strokeWidth="2" />
        </>
      )}
      {layout === "peninsula" && (
        <>
          <rect x="4" y="10" width="56" height="14" rx="2" stroke={stroke} strokeWidth="2" />
          <rect x="36" y="24" width="20" height="14" rx="2" stroke={stroke} strokeWidth="2" />
        </>
      )}
    </svg>
  );
}
