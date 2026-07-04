"use client";

import { AlertCircle, ArrowRight, Loader2, Lock, Shield, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Logo } from "@/components/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge, Button, Card, Input, Label } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function AdminLoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username.trim(), password, true);
      router.push("/admin");
    } catch (err: any) {
      setError(err?.message || "Admin login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="aurora flex min-h-screen items-center justify-center px-6">
      <div className="absolute right-6 top-6 z-10"><ThemeToggle /></div>

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 flex justify-center"><Logo /></div>

        <Card glass className="animate-fade-in p-8 shadow-glass">
          <div className="mb-6 text-center">
            <div className="mb-3 flex justify-center">
              <Badge tone="primary" className="gap-1.5"><Shield className="h-3.5 w-3.5" /> Admin Console</Badge>
            </div>
            <h1 className="text-xl font-semibold tracking-tight">Agency sign in</h1>
            <p className="mt-1 text-sm text-muted-foreground">Manage clients, integrations and reports</p>
          </div>

          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-danger/20 bg-danger/10 px-3 py-2.5 text-sm text-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{error}</span>
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">Admin username</Label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input id="username" autoComplete="username" className="pl-10" placeholder="admin"
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
            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Enter console <ArrowRight className="h-4 w-4" /></>}
            </Button>
          </form>

          <div className="mt-6 border-t border-border pt-4 text-center">
            <Link href="/login" className="text-xs text-muted-foreground hover:text-foreground">← Client sign in</Link>
          </div>
        </Card>

        <p className="mt-6 text-center text-sm text-muted-foreground">Powered by DiziGroww</p>
      </div>
    </div>
  );
}
