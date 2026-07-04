"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, apiPost, tokenStore } from "@/lib/api";

export type User = { id: string; email: string; username: string; role: "ADMIN" | "CLIENT" };

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string, admin?: boolean) => Promise<User>;
  logout: () => void;
  setToken: (access: string, refresh?: string) => Promise<void>;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api<User>("/auth/me");
      setUser(me);
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const login = useCallback(async (username: string, password: string, admin = false) => {
    const path = admin ? "/auth/admin/login" : "/auth/login";
    const tokens = await apiPost<{ access_token: string; refresh_token: string }>(path, { username, password });
    tokenStore.set(tokens.access_token, tokens.refresh_token);
    const me = await api<User>("/auth/me");
    setUser(me);
    return me;
  }, []);

  const setToken = useCallback(async (access: string, refresh?: string) => {
    tokenStore.set(access, refresh);
    await loadMe();
  }, [loadMe]);

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    if (typeof window !== "undefined") window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
