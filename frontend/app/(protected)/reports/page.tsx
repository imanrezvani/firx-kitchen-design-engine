"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { toJalali, LAYOUT_FA, faNumber } from "@/lib/format";
import { Card, CardBody, CardHeader, CardTitle, Badge } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/field";

interface DesignRow {
  id: string;
  project_id: string;
  name: string;
  layout: string;
  updated_at: string;
  total_retail?: number;
}

export default function ReportsPage() {
  const [designs, setDesigns] = useState<DesignRow[]>([]);
  const [projects, setProjects] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const stats = await apiGet<{ recent_designs: DesignRow[] }>("/api/v1/dashboard/stats");
        setDesigns(stats.recent_designs);
      } catch {
        /* ignore */
      }
      try {
        const ps = await apiGet<any[]>("/api/v1/projects");
        const map: Record<string, string> = {};
        ps.forEach((p) => (map[p.id] = p.name));
        setProjects(map);
      } catch {
        /* ignore */
      }
      setLoading(false);
    })();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">گزارش‌ها</h1>

      <Card>
        <CardHeader>
          <CardTitle>طراحی‌های اخیر</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <p className="p-5 text-muted-foreground">در حال بارگذاری...</p>
          ) : !designs.length ? (
            <EmptyState title="گزارشی برای نمایش نیست" description="پس از تولید اولین طرح، گزارش آن در اینجا دیده می‌شود" />
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="px-5 py-3">طرح</th>
                  <th className="px-5 py-3">پروژه</th>
                  <th className="px-5 py-3">چیدمان</th>
                  <th className="px-5 py-3">قیمت تخمینی</th>
                  <th className="px-5 py-3">آخرین به‌روزرسانی</th>
                  <th className="px-5 py-3 text-left">باز کردن</th>
                </tr>
              </thead>
              <tbody>
                {designs.map((d) => (
                  <tr key={d.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                    <td className="px-5 py-3 font-medium">{d.name}</td>
                    <td className="px-5 py-3 text-muted-foreground">{projects[d.project_id] || "—"}</td>
                    <td className="px-5 py-3">
                      <Badge>{LAYOUT_FA[d.layout] || d.layout}</Badge>
                    </td>
                    <td className="px-5 py-3 font-medium">
                      {d.total_retail ? `${faNumber(d.total_retail)} تومان` : "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">{toJalali(d.updated_at)}</td>
                    <td className="px-5 py-3 text-left">
                      <Link href={`/designer?design=${d.id}`}>
                        <Card className="inline-block px-3 py-1 text-xs font-medium text-primary hover:bg-muted/40">باز کردن</Card>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </CardBody>
      </Card>

      <p className="text-xs text-muted-foreground">
        گزارش‌های کامل مالی و تخمین متریال از بخش BOM هر طرح در دسترس است.
      </p>
    </div>
  );
}
