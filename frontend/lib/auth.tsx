"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api, clearToken, getToken, setToken } from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name?: string;
}

interface Tenant {
  id: string;
  name: string;
  company_name?: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    company_name: string;
    full_name: string;
    email: string;
    password: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api<{ user: User; tenant: Tenant | null }>("/api/v1/auth/me");
        setUser(me.user);
        setTenant(me.tenant);
      } catch {
        clearToken();
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function login(email: string, password: string) {
    const res = await api<{ access_token: string; user: User }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    setUser(res.user);
    const me = await api<{ user: User; tenant: Tenant | null }>("/api/v1/auth/me");
    setTenant(me.tenant);
  }

  async function register(data: {
    company_name: string;
    full_name: string;
    email: string;
    password: string;
  }) {
    const res = await api<{ access_token: string; user: User }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setToken(res.access_token);
    setUser(res.user);
    const me = await api<{ user: User; tenant: Tenant | null }>("/api/v1/auth/me");
    setTenant(me.tenant);
  }

  function logout() {
    clearToken();
    setUser(null);
    setTenant(null);
    window.location.href = "/login";
  }

  return (
    <AuthContext.Provider value={{ user, tenant, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
