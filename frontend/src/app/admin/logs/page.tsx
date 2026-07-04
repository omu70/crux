"use client";

import { CheckCircle2, CircleSlash } from "lucide-react";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useApiStatus, useAuditLogs } from "@/lib/hooks";

export default function LogsPage() {
  const logs = useAuditLogs();
  const status = useApiStatus();

  return (
    <div className="space-y-6">
      <PageHeader title="Activity & API" subtitle="Audit trail and integration health" />

      <Card>
        <CardHeader><CardTitle>API Status</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {status.data && Object.entries(status.data).map(([k, v]: any) => (
            <div key={k} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
              <span className="capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span>
              {v === "connected" ? <Badge tone="success"><CheckCircle2 className="mr-1 h-3 w-3" /> Live</Badge> : <Badge><CircleSlash className="mr-1 h-3 w-3" /> Not set</Badge>}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Audit Log</CardTitle></CardHeader>
        <CardContent className="p-0">
          {logs.isLoading ? <Loading /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="p-3 font-medium">Action</th>
                    <th className="p-3 font-medium">Entity</th>
                    <th className="p-3 font-medium">IP</th>
                    <th className="p-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {(logs.data ?? []).map((a: any) => (
                    <tr key={a.id} className="border-b border-border/60 last:border-0">
                      <td className="p-3 font-medium capitalize">{a.action.replace(/_/g, " ")}</td>
                      <td className="p-3 text-muted-foreground">{a.entity ?? "—"}</td>
                      <td className="p-3 text-muted-foreground tabular">{a.ip ?? "—"}</td>
                      <td className="p-3 text-muted-foreground">{new Date(a.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
