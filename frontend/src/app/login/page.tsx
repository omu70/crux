"use client";

import { AlertCircle, ArrowRight, Loader2, Lock, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Logo } from "@/components/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button, Card, Input, Label } from "@/components/ui";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const me = await login(username.trim(), password);
      router.push(me.role === "ADMIN" ? "/admin" : "/dashboard");
    } catch (err: any) {
      setError(err?.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function onForgot() {
    if (!username.trim()) return setError("Enter your username first, then tap Forgot password.");
    setError("");
    try {
      await apiPost("/auth/forgot-password", { username: username.trim() });
      setNotice("If that account exists, reset instructions have been sent to your account manager.");
    } catch {
      setNotice("If that account exists, reset instructions have been sent.");
    }
  }

  return (
    <div className="aurora flex min-h-screen items-center justify-center px-6">
      <div className="absolute right-6 top-6 z-10"><ThemeToggle /></div>

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 flex justify-center"><Logo /></div>

        <Card glass className="animate-fade-in p-8 shadow-glass">
          <div className="mb-6 text-center">
            <h1 className="text-xl font-semibold tracking-tight">Welcome back</h1>
            <p className="mt-1 text-sm text-muted-foreground">Sign in to your client portal</p>
          </div>

          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-danger/20 bg-danger/10 px-3 py-2.5 text-sm text-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{error}</span>
            </div>
          )}
          {notice && (
            <div className="mb-4 rounded-lg border border-success/20 bg-success/10 px-3 py-2.5 text-sm text-success">{notice}</div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input id="username" autoComplete="username" className="pl-10" placeholder="yourcompany"
                  value={username} onChange={(e) => setUsername(e.target.value)} required />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input id="password" type="password" autoComplete="current-password" className="pl-10" placeholder="••••••••"
                  value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex cursor-pointer items-center gap-2 text-muted-foreground">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 rounded border-border accent-[hsl(var(--primary))]" />
                Remember me
              </label>
              <button type="button" onClick={onForgot} className="font-medium text-primary hover:underline">
                Forgot password?
              </button>
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Login <ArrowRight className="h-4 w-4" /></>}
            </Button>
          </form>

          <div className="mt-6 border-t border-border pt-4 text-center">
            <Link href="/admin/login" className="text-xs text-muted-foreground hover:text-foreground">
              Admin sign in →
            </Link>
          </div>
        </Card>

        <p className="mt-6 text-center text-sm text-muted-foreground">Powered by DiziGroww</p>
      </div>
    </div>
  );
}
