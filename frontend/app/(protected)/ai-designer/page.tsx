"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { faNumber } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { Card, CardBody, CardHeader, CardTitle, Badge } from "@/components/ui/card";
import { SpatialEditor } from "@/components/designer/spatial-editor";
import { DesignCanvas } from "@/components/designer/design-canvas";
import {
  DEFAULT_SPEC,
  LayoutKind,
  StyleKind,
  STYLE_FA,
  LAYOUT_FA,
  syncWalls,
  type ApplianceSpec,
  type CabinetSpec,
  type DoorSpec,
  type KitchenSpecification,
  type ObjectPosition,
  type WallSide,
  type WindowSpec,
} from "@/lib/ai-spec";
import { runPipeline, type DesignSpecification, type PipelineResult } from "@/lib/ai-api";

interface Project {
  id: string;
  name: string;
}

interface PhotoUpload {
  url: string;
  caption: string;
}

const LAYOUT_ORDER: LayoutKind[] = [
  LayoutKind.SINGLE_WALL,
  LayoutKind.L_SHAPE,
  LayoutKind.U_SHAPE,
  LayoutKind.G_SHAPE,
  LayoutKind.ISLAND,
  LayoutKind.PENINSULA,
];

const CABINET_TYPES: { type: CabinetSpec["type"]; fa: string }[] = [
  { type: "base", fa: "پایه" },
  { type: "wall", fa: "دیواری" },
  { type: "tall", fa: "بلند" },
  { type: "corner", fa: "گوشه" },
  { type: "drawer", fa: "کشو" },
];

const APPLIANCE_TYPES: { type: ApplianceSpec["type"]; fa: string; variants: { value: string; fa: string }[] }[] = [
  {
    type: "refrigerator",
    fa: "یخچال",
    variants: [
      { value: "double_door", fa: "درب دو" },
      { value: "single_door", fa: "درب یک" },
      { value: "side_by_side", fa: "کنار هم" },
      { value: "built_in", fa: "توکار" },
    ],
  },
  {
    type: "dishwasher",
    fa: "ظرف‌شویی",
    variants: [
      { value: "60cm", fa: "۶۰ سانتی" },
      { value: "45cm", fa: "۴۵ سانتی" },
    ],
  },
  {
    type: "washing_machine",
    fa: "لباسشویی",
    variants: [
      { value: "front_load", fa: "لباسشویی از جلو" },
      { value: "top_load", fa: "لباسشویی از بالا" },
    ],
  },
  {
    type: "oven",
    fa: "فر",
    variants: [
      { value: "built_in", fa: "توکار" },
      { value: "countertop", fa: "رومیزی" },
    ],
  },
  {
    type: "cooktop",
    fa: "اجاق گاز",
    variants: [
      { value: "built_in", fa: "توکار" },
      { value: "freestanding", fa: "ایستاده" },
    ],
  },
  {
    type: "hood",
    fa: "هود",
    variants: [
      { value: "wall_mounted", fa: "دیواری" },
      { value: "built_in", fa: "توکار" },
      { value: "island", fa: "جزیره‌ای" },
    ],
  },
];

const WALLS: { value: WallSide; fa: string }[] = [
  { value: "north", fa: "شمال" },
  { value: "south", fa: "جنوب" },
  { value: "east", fa: "شرق" },
  { value: "west", fa: "غرب" },
];

export default function AiDesignerPage() {
  const [spec, setSpec] = useState<KitchenSpecification>(() =>
    syncWalls({ ...DEFAULT_SPEC, walls: [] }),
  );
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [photos, setPhotos] = useState<PhotoUpload[]>([]);
  const [photoUrl, setPhotoUrl] = useState("");
  const [photoCaption, setPhotoCaption] = useState("");
  const [notes, setNotes] = useState("");
  const [preferences, setPreferences] = useState("");
  const [mustInclude, setMustInclude] = useState("");
  const [mustAvoid, setMustAvoid] = useState("");
  const [openForm, setOpenForm] = useState<null | "door" | "window">(null);
  const [oForm, setOForm] = useState<{ wall: WallSide; offset: number; width: number; height: number; sill: number }>({
    wall: "north",
    offset: 200,
    width: 900,
    height: 2100,
    sill: 900,
  });
  const [cabForm, setCabForm] = useState<{ type: CabinetSpec["type"]; width: number; height: number; depth: number; count: number }>({
    type: "base",
    width: 600,
    height: 720,
    depth: 600,
    count: 4,
  });
  const [appForm, setAppForm] = useState<{ type: ApplianceSpec["type"]; variant: string }>({
    type: "refrigerator",
    variant: "double_door",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [provider, setProvider] = useState<"mock" | "gpt" | "gemini">("mock");

  async function loadProjects() {
    try {
      setProjects(await apiGet<Project[]>("/api/v1/projects"));
    } catch {
      // non-fatal — user can proceed without a linked project
    }
  }

  function patchRoom(key: "width" | "length" | "height", value: number) {
    setSpec((s) => syncWalls({ ...s, room: { ...s.room, [key]: value } }));
  }

  function addOpening() {
    if (!openForm) return;
    const base = {
      wall: oForm.wall,
      offset: oForm.offset,
      width: oForm.width,
      height: oForm.height,
      id: Math.random().toString(36).slice(2),
    };
    if (openForm === "door") {
      setSpec((s) => ({ ...s, doors: [...s.doors, base as DoorSpec] }));
    } else {
      setSpec((s) => ({
        ...s,
        windows: [...s.windows, { ...base, sill_height: oForm.sill } as WindowSpec],
      }));
    }
    setOpenForm(null);
  }

  function removeOpening(kind: "door" | "window", id: string) {
    setSpec((s) => ({
      ...s,
      doors: kind === "door" ? s.doors.filter((d) => d.id !== id) : s.doors,
      windows: kind === "window" ? s.windows.filter((w) => w.id !== id) : s.windows,
    }));
  }

  function addCabinet() {
    setSpec((s) => ({ ...s, cabinets: [...s.cabinets, { ...cabForm }] }));
  }

  function removeCabinet(i: number) {
    setSpec((s) => ({ ...s, cabinets: s.cabinets.filter((_, idx) => idx !== i) }));
  }

  function addAppliance() {
    setSpec((s) => ({
      ...s,
      appliances: [...s.appliances, { type: appForm.type, variant: appForm.variant as ApplianceSpec["variant"] }],
    }));
  }

  function removeAppliance(i: number) {
    setSpec((s) => ({ ...s, appliances: s.appliances.filter((_, idx) => idx !== i) }));
  }

  function addPhoto() {
    if (!photoUrl.trim()) return;
    setPhotos((p) => [...p, { url: photoUrl.trim(), caption: photoCaption.trim() }]);
    setPhotoUrl("");
    setPhotoCaption("");
  }

  function buildSpec(): KitchenSpecification {
    const req = {
      notes,
      preferences: preferences.split("\n").map((s) => s.trim()).filter(Boolean),
      must_include: mustInclude.split("\n").map((s) => s.trim()).filter(Boolean),
      must_avoid: mustAvoid.split("\n").map((s) => s.trim()).filter(Boolean),
    };
    return {
      ...spec,
      project_id: projectId,
      photos: photos.map((p, i) => ({ id: `ph-${i}`, url: p.url, caption: p.caption || null })),
      user_requirements: req,
    };
  }

  async function generate() {
    setError("");
    setNotice("");
    setLoading(true);
    try {
      const payload = buildSpec();
      const res = await runPipeline(payload, provider);
      setResult(res);
      setNotice("طراحی با موفقیت تولید شد.");
    } catch (e: any) {
      setError(e.message || "خطا در اجرای خط لوله هوش مصنوعی");
    } finally {
      setLoading(false);
    }
  }

  async function saveDesign() {
    if (!result || !projectId) {
      setError("برای ذخیره طرح ابتدا یک پروژه انتخاب کنید.");
      return;
    }
    setLoading(true);
    try {
      const d = result.design;
      const created = await apiPost<any>(`/api/v1/projects/${projectId}/designs/generate`, {
        room_id: null,
        layout: result.spec.layout.toLowerCase(),
        countertop_material_id: null,
        cabinet_material_id: null,
        ai: {
          score: d.score,
          rationale: d.rationale,
          warnings: d.warnings,
          render_instructions: d.render_instructions,
        },
      });
      setNotice(`طرح در پروژه ذخیره شد. (${faNumber(d.score)} امتیاز)`);
      void created;
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">طراحی هوشمند آشپزخانه</h1>
        <div className="flex items-center gap-3">
          <Select className="w-36" value={provider} onChange={(e) => setProvider(e.target.value as any)}>
            <option value="mock">شبیه‌ساز (Mock)</option>
            <option value="gpt">GPT</option>
            <option value="gemini">Gemini</option>
          </Select>
          <Badge color="blue">خط لولهٔ قطعی + تست‌پذیر</Badge>
        </div>
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}
      {notice && <p className="rounded-lg bg-success/10 px-3 py-2 text-sm text-success">{notice}</p>}

      <div className="grid grid-cols-3 gap-4">
        {/* Room */}
        <Card>
          <CardHeader>
            <CardTitle>فضا</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <Field label="پروژه">
              <Select value={projectId} onChange={(e) => setProjectId(e.target.value)} onClick={loadProjects as any}>
                <option value="">(اختیاری) انتخاب پروژه...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="grid grid-cols-3 gap-2">
              <Field label="عرض">
                <Input type="number" value={spec.room.width} onChange={(e) => patchRoom("width", +e.target.value)} />
              </Field>
              <Field label="طول">
                <Input type="number" value={spec.room.length} onChange={(e) => patchRoom("length", +e.target.value)} />
              </Field>
              <Field label="ارتفاع">
                <Input type="number" value={spec.room.height} onChange={(e) => patchRoom("height", +e.target.value)} />
              </Field>
            </div>
            <Field label="چیدمان">
              <div className="grid grid-cols-2 gap-2">
                {LAYOUT_ORDER.map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setSpec((s) => ({ ...s, layout: l }))}
                    className={`rounded-lg border px-2 py-2 text-xs transition-colors ${
                      spec.layout === l ? "border-primary bg-primary/10 font-bold text-primary" : "border-border hover:border-primary/40"
                    }`}
                  >
                    {LAYOUT_FA[l]}
                  </button>
                ))}
              </div>
            </Field>
            <Field label="سبک">
              <Select
                value={spec.style}
                onChange={(e) => setSpec((s) => ({ ...s, style: e.target.value as StyleKind }))}
              >
                {(Object.keys(StyleKind) as StyleKind[]).map((k) => (
                  <option key={k} value={k}>
                    {STYLE_FA[k as StyleKind]}
                  </option>
                ))}
              </Select>
            </Field>
          </CardBody>
        </Card>

        {/* Openings */}
        <Card>
          <CardHeader>
            <CardTitle>درها و پنجره‌ها</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" type="button" onClick={() => { setOForm({ ...oForm, height: 2100, sill: 0 }); setOpenForm("door"); }}>
                + درب
              </Button>
              <Button variant="outline" size="sm" type="button" onClick={() => { setOForm({ ...oForm, height: 1500, sill: 900 }); setOpenForm("window"); }}>
                + پنجره
              </Button>
            </div>

            {openForm && (
              <div className="space-y-3 rounded-xl border border-border bg-muted/20 p-3">
                <p className="text-sm font-bold">{openForm === "door" ? "درب جدید" : "پنجره جدید"}</p>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="دیوار">
                    <Select value={oForm.wall} onChange={(e) => setOForm({ ...oForm, wall: e.target.value as WallSide })}>
                      {WALLS.map((w) => (
                        <option key={w.value} value={w.value}>
                          {w.fa}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="فاصله (mm)">
                    <Input type="number" value={oForm.offset} onChange={(e) => setOForm({ ...oForm, offset: +e.target.value })} />
                  </Field>
                  <Field label="عرض (mm)">
                    <Input type="number" value={oForm.width} onChange={(e) => setOForm({ ...oForm, width: +e.target.value })} />
                  </Field>
                  <Field label="ارتفاع (mm)">
                    <Input type="number" value={oForm.height} onChange={(e) => setOForm({ ...oForm, height: +e.target.value })} />
                  </Field>
                  {openForm === "window" && (
                    <Field label="ارتفاع عتبه (mm)">
                      <Input type="number" value={oForm.sill} onChange={(e) => setOForm({ ...oForm, sill: +e.target.value })} />
                    </Field>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={addOpening}>افزودن</Button>
                  <Button variant="ghost" size="sm" onClick={() => setOpenForm(null)}>انصراف</Button>
                </div>
              </div>
            )}

            {spec.doors.map((d) => (
              <div key={d.id} className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2 text-sm">
                <span>درب · {d.wall} · {faNumber(d.offset)}mm</span>
                <button className="text-danger" onClick={() => removeOpening("door", d.id!)}>×</button>
              </div>
            ))}
            {spec.windows.map((w) => (
              <div key={w.id} className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2 text-sm">
                <span>پنجره · {w.wall} · {faNumber(w.offset)}mm</span>
                <button className="text-danger" onClick={() => removeOpening("window", w.id!)}>×</button>
              </div>
            ))}
          </CardBody>
        </Card>

        {/* Cabinets & Appliances */}
        <Card>
          <CardHeader>
            <CardTitle>کابینت و لوازم</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="rounded-xl border border-border bg-muted/20 p-3">
              <p className="mb-2 text-sm font-bold">افزودن کابینت</p>
              <div className="grid grid-cols-2 gap-2">
                <Field label="نوع">
                  <Select value={cabForm.type} onChange={(e) => setCabForm({ ...cabForm, type: e.target.value as any })}>
                    {CABINET_TYPES.map((c) => (
                      <option key={c.type} value={c.type}>{c.fa}</option>
                    ))}
                  </Select>
                </Field>
                <Field label="تعداد">
                  <Input type="number" value={cabForm.count} onChange={(e) => setCabForm({ ...cabForm, count: +e.target.value })} />
                </Field>
                <Field label="عرض (mm)">
                  <Input type="number" value={cabForm.width} onChange={(e) => setCabForm({ ...cabForm, width: +e.target.value })} />
                </Field>
                <Field label="ارتفاع (mm)">
                  <Input type="number" value={cabForm.height} onChange={(e) => setCabForm({ ...cabForm, height: +e.target.value })} />
                </Field>
                <Field label="عمق (mm)">
                  <Input type="number" value={cabForm.depth} onChange={(e) => setCabForm({ ...cabForm, depth: +e.target.value })} />
                </Field>
              </div>
              <Button className="mt-2" size="sm" onClick={addCabinet}>+ کابینت</Button>
              {spec.cabinets.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {spec.cabinets.map((c, i) => (
                    <li key={i} className="flex items-center justify-between rounded-lg bg-white px-2 py-1 text-xs">
                      <span>
                        {CABINET_TYPES.find((x) => x.type === c.type)?.fa} · {faNumber(c.width)}×{faNumber(c.depth)} · ×{faNumber(c.count)}
                      </span>
                      <button className="text-danger" onClick={() => removeCabinet(i)}>×</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-xl border border-border bg-muted/20 p-3">
              <p className="mb-2 text-sm font-bold">افزودن وسیله</p>
              <div className="grid grid-cols-2 gap-2">
                <Field label="وسیله">
                  <Select
                    value={appForm.type}
                    onChange={(e) => {
                      const t = e.target.value as ApplianceSpec["type"];
                      const def = APPLIANCE_TYPES.find((a) => a.type === t);
                      setAppForm({ type: t, variant: def?.variants[0]?.value || "built_in" });
                    }}
                  >
                    {APPLIANCE_TYPES.map((a) => (
                      <option key={a.type} value={a.type}>{a.fa}</option>
                    ))}
                  </Select>
                </Field>
                <Field label="نوع">
                  <Select
                    value={appForm.variant}
                    onChange={(e) => setAppForm({ ...appForm, variant: e.target.value })}
                  >
                    {APPLIANCE_TYPES.find((a) => a.type === appForm.type)?.variants.map((v) => (
                      <option key={v.value} value={v.value}>{v.fa}</option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Button className="mt-2" size="sm" onClick={addAppliance}>+ وسیله</Button>
              {spec.appliances.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {spec.appliances.map((a, i) => (
                    <li key={i} className="flex items-center justify-between rounded-lg bg-white px-2 py-1 text-xs">
                      <span>{APPLIANCE_TYPES.find((x) => x.type === a.type)?.fa}</span>
                      <button className="text-danger" onClick={() => removeAppliance(i)}>×</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Spatial editor */}
      <Card>
        <CardHeader>
          <CardTitle>ویرایشگر فضایی — جای‌گذاری لوازم</CardTitle>
        </CardHeader>
        <CardBody>
          <SpatialEditor
            width={spec.room.width}
            length={spec.room.length}
            objects={spec.objects}
            onChange={(objects: ObjectPosition[]) => setSpec((s) => ({ ...s, objects }))}
          />
        </CardBody>
      </Card>

      {/* Photos & requirements */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>عکس‌های محیط</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            <div className="flex gap-2">
              <Input placeholder="URL عکس" value={photoUrl} onChange={(e) => setPhotoUrl(e.target.value)} />
              <Input placeholder="توضیح" value={photoCaption} onChange={(e) => setPhotoCaption(e.target.value)} />
              <Button variant="outline" size="sm" onClick={addPhoto}>+</Button>
            </div>
            {photos.map((p, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2 text-xs">
                <span className="truncate">{p.url}</span>
                <button className="text-danger" onClick={() => setPhotos(photos.filter((_, idx) => idx !== i))}>×</button>
              </div>
            ))}
            <p className="text-xs text-muted-foreground">عکس‌ها اطلاعات جانبی هستند؛ منبع حقیقت، مشخصات ساخت‌یافته است.</p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>نیازمندی‌های کاربر</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            <Field label="یادداشت‌ها">
              <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="مثلاً: خانواده چهار نفره" />
            </Field>
            <Field label="ترجیحات (هر خط یک مورد)">
              <Textarea rows={2} value={preferences} onChange={(e) => setPreferences(e.target.value)} />
            </Field>
            <Field label="باید شامل شود">
              <Textarea rows={2} value={mustInclude} onChange={(e) => setMustInclude(e.target.value)} />
            </Field>
            <Field label="نباید شامل شود">
              <Textarea rows={2} value={mustAvoid} onChange={(e) => setMustAvoid(e.target.value)} />
            </Field>
          </CardBody>
        </Card>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={generate} disabled={loading}>
          {loading ? "در حال تولید..." : "تولید طرح با هوش مصنوعی"}
        </Button>
        {result && (
          <Button variant="outline" onClick={saveDesign} disabled={loading || !projectId}>
            ذخیره در پروژه
          </Button>
        )}
      </div>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                نتیجه — {result.design.layout} · {result.design.style}
                <Badge color={result.design.score >= 90 ? "green" : "amber"}>امتیاز {faNumber(result.design.score)}</Badge>
              </CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <DesignCanvas design={toCanvasView(result.design)} />
              <p className="rounded-lg bg-muted/30 px-3 py-2 text-sm">{result.design.rationale}</p>
              {result.design.warnings.length > 0 && (
                <ul className="space-y-1 text-sm text-warning">
                  {result.design.warnings.map((w, i) => (
                    <li key={i}>! {w}</li>
                  ))}
                </ul>
              )}
              <div className="grid grid-cols-3 gap-2">
                <Stat label="کابینت" value={faNumber(result.design.cabinets.length)} />
                <Stat label="لوازم" value={faNumber(result.design.appliances.length)} />
                <Stat label="صفحه‌ها" value={faNumber(result.design.countertops.length)} />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>پرامپت ارسالی ({faNumber(result.prompt.sections.length)} بخش ثابت)</CardTitle>
            </CardHeader>
            <CardBody className="space-y-3">
              <p className="text-xs text-muted-foreground">دوربین‌ها: {result.prompt.camera_views.join("، ")}</p>
              <pre className="max-h-96 overflow-auto rounded-xl bg-muted/30 p-4 text-xs whitespace-pre-wrap">
                {result.prompt.sections.map((s) => `## ${s.title}\n${s.body}`).join("\n\n")}
              </pre>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-muted/20 p-3 text-center">
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function toCanvasView(d: DesignSpecification) {
  return {
    room: {
      width_mm: Number(d.room.width ?? 0),
      length_mm: Number(d.room.length ?? 0),
      height_mm: Number(d.room.height ?? 0),
    },
    cabinets: d.cabinets.map((c) => ({
      id: c.id,
      type: c.type,
      name: c.name,
      width_mm: c.width_mm,
      height_mm: c.height_mm,
      depth_mm: c.depth_mm,
      x: c.x,
      y: c.y,
      rotation: c.rotation,
    })),
    appliances: d.appliances.map((a) => ({
      id: a.id,
      appliance_type: a.type,
      name: a.name,
      width_mm: a.width_mm,
      height_mm: a.height_mm,
      depth_mm: a.depth_mm,
      x: a.x,
      y: a.y,
      rotation: a.rotation,
    })),
    countertops: d.countertops.map((c) => ({
      id: c.id,
      width_mm: c.width_mm,
      depth_mm: c.depth_mm,
      x: c.x,
      y: c.y,
    })),
    layout: d.layout,
  };
}
