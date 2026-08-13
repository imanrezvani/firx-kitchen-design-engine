"use client";

import { useAuth } from "@/lib/auth";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const { tenant, user } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">تنظیمات</h1>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>سازمان</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">نام شرکت</span>
              <span>{tenant?.company_name || tenant?.name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">نقش شما</span>
              <span>{tenant?.role === "admin" ? "مدیر" : tenant?.role || "—"}</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>حساب کاربری</CardTitle>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">نام</span>
              <span>{user?.full_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">ایمیل</span>
              <span dir="ltr">{user?.email}</span>
            </div>
          </CardBody>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">
        قابلیت‌های کامل مدیریت سازمان، اعضا و صورتحساب در نسخه‌های آینده پلتفرم ارائه خواهد شد.
      </p>
    </div>
  );
}
