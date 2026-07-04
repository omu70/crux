"use client";

import { CheckCircle2, CircleSlash, Users } from "lucide-react";
import { Loading, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useAdminOverview, useApiStatus } from "@/lib/hooks";
import { formatCurrency } from "@/lib/utils";

export default function AdminOverviewPage() {
  const overview = useAdminOverview();
  const status = useApiStatus();
  if (overview.isLoading) return <Loading />;
  const o = overview.data!;

  return (
    <div className="space-y-6">
      <PageHeader title="Agency Overview" subtitle="All clients at a glance" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Total Clients" value={o.clients.total} icon={Users} />
        <StatTile label="Active" value={o.clients.active} />
        <StatTile label="Suspended" value={o.clients.suspended} />
        <StatTile label="Tracked Revenue" value={formatCurrency(o.tracked_revenue, "USD", true)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Integration & API Status</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-2">
            {status.data && Object.entries(status.data).map(([k, v]: any) => (
              <div key={k} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
                <span className="capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span>
                {v === "connected" ? (
                  <Badge tone="success"><CheckCircle2 className="mr-1 h-3 w-3" /> Live</Badge>
                ) : (
                  <Badge><CircleSlash className="mr-1 h-3 w-3" /> Not set</Badge>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {(o.recent_activity ?? []).map((a: any, i: number) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="capitalize">{a.action.replace(/_/g, " ")}</span>
                <span className="text-xs text-muted-foreground">{new Date(a.created_at).toLocaleString()}</span>
              </div>
            ))}
            {(o.recent_activity ?? []).length === 0 && <p className="text-sm text-muted-foreground">No activity yet.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
