"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { AppShell } from "@/components/layout/app-shell";
import Dashboard from "./(protected)/page";

export default function Home() {
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setAuthed(true);
    }
  }, [router]);

  if (authed === null) return null;

  return (
    <AppShell>
      <Dashboard />
    </AppShell>
  );
}
