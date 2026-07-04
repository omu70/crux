"use client";

import { Gauge, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useSummary, useWebsiteHealth } from "@/lib/hooks";
import { formatCurrency } from "@/lib/utils";

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const summary = useSummary("30d");
  const health = useWebsiteHealth();

  if (summary.isLoading) return <Loading />;
  const c = summary.data!.client;

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Your account & workspace" />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Account</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Company" value={c.company_name} />
            <Row label="Contact" value={c.contact_name} />
            <Row label="Username" value={user?.username ?? "—"} />
            <Row label="Plan" value={<Badge tone="primary">{c.plan}</Badge>} />
            <Row label="Monthly Budget" value={formatCurrency(c.monthly_budget, c.currency)} />
            {c.account_manager && <Row label="Account Manager" value={`${c.account_manager.name} · ${c.account_manager.title}`} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Appearance</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Button variant={theme === "light" ? "primary" : "outline"} size="sm" onClick={() => setTheme("light")}><Sun className="h-4 w-4" /> Light</Button>
              <Button variant={theme === "dark" ? "primary" : "outline"} size="sm" onClick={() => setTheme("dark")}><Moon className="h-4 w-4" /> Dark</Button>
            </div>
            <p className="text-xs text-muted-foreground">Your theme preference is saved on this device.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Gauge className="h-4 w-4 text-primary" /> Website Health</CardTitle></CardHeader>
        <CardContent>
          {health.isLoading ? <Loading /> : health.data && Object.keys(health.data).length ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[["Performance", health.data.performance], ["Accessibility", health.data.accessibility], ["SEO", health.data.seo], ["Best Practices", health.data.best_practices]].map(([l, v]: any) => (
                <div key={l} className="rounded-lg border border-border p-4 text-center">
                  <div className="text-2xl font-semibold tabular">{v}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{l}</div>
                </div>
              ))}
              <div className="col-span-2 rounded-lg border border-border p-4 text-sm text-muted-foreground sm:col-span-4">
                Core Web Vitals — LCP {health.data.core_web_vitals?.lcp}s · FID {health.data.core_web_vitals?.fid}ms · CLS {health.data.core_web_vitals?.cls}
              </div>
            </div>
          ) : <p className="text-sm text-muted-foreground">No website health data yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
