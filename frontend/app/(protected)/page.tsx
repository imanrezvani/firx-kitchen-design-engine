"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { faNumber, toJalali, STATUS_FA, LAYOUT_FA } from "@/lib/format";
import { Card, CardBody, CardHeader, CardTitle, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/field";

interface Stats {
  total_projects: number;
  active_projects: number;
  customers: number;
  designs: number;
  recent_projects: { id: string; name: string; status: string; created_at: string }[];
  recent_designs: { id: string; project_id: string; name: string; layout: string; updated_at: string; total_retail?: number }[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<Stats>("/api/v1/dashboard/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  const cards = [
    { label: "کل پروژه‌ها", value: stats?.total_projects ?? null, color: "text-primary" },
    { label: "پروژه‌های فعال", value: stats?.active_projects ?? null, color: "text-blue-600" },
    { label: "مشتریان", value: stats?.customers ?? null, color: "text-success" },
    { label: "طراحی‌ها", value: stats?.designs ?? null, color: "text-warning" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">داشبورد</h1>
        <Link href="/designer">
          <Button>+ طراحی جدید</Button>
        </Link>
      </div>

      {error && <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}

      <div className="grid grid-cols-4 gap-4">
        {cards.map((c) => (
          <Card key={c.label}>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{c.label}</p>
                <p className={`mt-1 text-3xl font-bold ${c.color}`}>{faNumber(c.value)}</p>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>پروژه‌های اخیر</CardTitle>
            <Link href="/projects" className="text-xs text-primary hover:underline">
              مشاهده همه
            </Link>
          </CardHeader>
          <CardBody className="p-0">
            {!stats?.recent_projects?.length ? (
              <EmptyState title="پروژه‌ای ثبت نشده" description="اولین پروژه خود را بسازید" />
            ) : (
              <ul className="divide-y divide-border">
                {stats.recent_projects.map((p) => {
                  const st = STATUS_FA[p.status] || STATUS_FA.draft;
                  return (
                    <li key={p.id} className="flex items-center justify-between px-5 py-3">
                      <div>
                        <Link href={`/projects/${p.id}`} className="text-sm font-medium hover:text-primary">
                          {p.name}
                        </Link>
                        <p className="text-xs text-muted-foreground">{toJalali(p.created_at)}</p>
                      </div>
                      <Badge color={st.color as any}>{st.label}</Badge>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>طراحی‌های اخیر</CardTitle>
          </CardHeader>
          <CardBody className="p-0">
            {!stats?.recent_designs?.length ? (
              <EmptyState title="طراحی‌ای انجام نشده" description="از بخش طراحی آشپزخانه شروع کنید" />
            ) : (
              <ul className="divide-y divide-border">
                {stats.recent_designs.map((d) => (
                  <li key={d.id} className="flex items-center justify-between px-5 py-3">
                    <div>
                      <p className="text-sm font-medium">{d.name}</p>
                      <p className="text-xs text-muted-foreground">
                        چیدمان {LAYOUT_FA[d.layout] || d.layout} · {toJalali(d.updated_at)}
                        {typeof d.total_retail === "number" && d.total_retail > 0 && (
                          <> · قیمت تخمینی <b className="text-foreground">{faNumber(d.total_retail)}</b> تومان</>
                        )}
                      </p>
                    </div>
                    <Link href={`/designer?design=${d.id}`}>
                      <Button variant="outline" size="sm">
                        باز کردن
                      </Button>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
