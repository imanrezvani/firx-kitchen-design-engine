"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiGet } from "@/lib/api";
import { faNumber, toJalali, STATUS_FA, LAYOUT_FA } from "@/lib/format";
import { Card, CardBody, CardHeader, CardTitle, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/field";

interface Project {
  id: string;
  name: string;
  status: string;
  notes?: string | null;
  created_at: string;
}

interface Room {
  id: string;
  name: string;
  width_mm: number;
  length_mm: number;
  height_mm: number;
  openings: any[];
}

interface DesignRow {
  id: string;
  name: string;
  layout: string;
  current_version?: number;
  updated_at: string;
  total_retail?: number;
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [designs, setDesigns] = useState<DesignRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setProject(await apiGet<Project>(`/api/v1/projects/${id}`));
        setRoom(await apiGet<Room | null>(`/api/v1/projects/${id}/room`));
        setDesigns(await apiGet<DesignRow[]>(`/api/v1/projects/${id}/designs`));
      } catch (e: any) {
        setError(e.message);
      }
    })();
  }, [id]);

  if (!project)
    return <p className="text-muted-foreground">{error || "در حال بارگذاری..."}</p>;

  const st = STATUS_FA[project.status] || STATUS_FA.draft;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/projects" className="text-muted-foreground hover:text-foreground">→</Link>
          <h1 className="text-xl font-bold">{project.name}</h1>
          <Badge color={st.color as any}>{st.label}</Badge>
        </div>
        <Link href={`/designer?project=${project.id}`}>
          <Button>طراحی آشپزخانه</Button>
        </Link>
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>اطلاعات پروژه</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">وضعیت</span>
              <span>{st.label}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">تاریخ ایجاد</span>
              <span>{toJalali(project.created_at)}</span>
            </div>
            {project.notes && (
              <p className="rounded-lg bg-muted/40 px-2 py-1 text-xs">{project.notes}</p>
            )}
          </CardBody>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>فضای آشپزخانه</CardTitle>
          </CardHeader>
          <CardBody>
            {!room ? (
              <EmptyState
                title="فضایی ثبت نشده"
                description="با طراحی آشپزخانه شروع کنید تا فضای پروژه ساخته شود"
              />
            ) : (
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="rounded-xl bg-muted/30 p-4 text-center">
                  <p className="text-2xl font-bold">{faNumber(room.width_mm)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">عرض (میلی‌متر)</p>
                </div>
                <div className="rounded-xl bg-muted/30 p-4 text-center">
                  <p className="text-2xl font-bold">{faNumber(room.length_mm)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">طول (میلی‌متر)</p>
                </div>
                <div className="rounded-xl bg-muted/30 p-4 text-center">
                  <p className="text-2xl font-bold">{faNumber(room.height_mm)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">ارتفاع (میلی‌متر)</p>
                </div>
                <div className="col-span-3 rounded-xl bg-muted/30 px-4 py-2 text-center text-xs text-muted-foreground">
                  بازشوها: {room.openings.length ? `${faNumber(room.openings.length)} مورد` : "—"}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>طراحی‌های پروژه</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          {!designs.length ? (
            <EmptyState
              title="طراحی‌ای ثبت نشده"
              description="از دکمه «طراحی آشپزخانه» برای ساخت اولین طرح استفاده کنید"
            />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="px-5 py-3">طرح</th>
                  <th className="px-5 py-3">چیدمان</th>
                  <th className="px-5 py-3">قیمت تخمینی</th>
                  <th className="px-5 py-3">آخرین به‌روزرسانی</th>
                  <th className="px-5 py-3 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {designs.map((d) => (
                  <tr key={d.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                    <td className="px-5 py-3 font-medium">{d.name}</td>
                    <td className="px-5 py-3">{LAYOUT_FA[d.layout] || d.layout}</td>
                    <td className="px-5 py-3 font-medium">
                      {d.total_retail ? `${faNumber(d.total_retail)} تومان` : "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">{toJalali(d.updated_at)}</td>
                    <td className="px-5 py-3 text-left">
                      <Link href={`/designer?design=${d.id}`}>
                        <Button variant="outline" size="sm">باز کردن</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
