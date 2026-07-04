"use client";

import { Download, FileText } from "lucide-react";
import { useState } from "react";
import { EmptyState, Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { apiGet } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useReports } from "@/lib/hooks";

export default function ReportsPage() {
  const { data, isLoading } = useReports();
  const [open, setOpen] = useState<any | null>(null);

  async function view(id: string) {
    setOpen(await apiGet(`/reports/${id}`));
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Reports" subtitle="Executive monthly performance reports" />

      {isLoading ? <Loading /> :
        (data ?? []).length === 0 ? <EmptyState icon={FileText} title="No reports yet" /> : (
          <div className="grid gap-3 sm:grid-cols-2">
            {(data ?? []).map((r: any) => (
              <Card key={r.id} className="flex items-center justify-between p-4">
                <div>
                  <div className="font-medium">{r.title}</div>
                  <div className="text-xs text-muted-foreground">{r.month}</div>
                </div>
                <Button variant="outline" size="sm" onClick={() => view(r.id)}>View</Button>
              </Card>
            ))}
          </div>
        )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setOpen(null)}>
          <Card className="max-h-[85vh] w-full max-w-2xl overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="text-base text-foreground">{open.title}</CardTitle>
              <Button size="sm" variant="secondary" onClick={() => window.print()}><Download className="h-4 w-4" /> Export PDF</Button>
            </CardHeader>
            <CardContent className="space-y-5 text-sm">
              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Executive Summary</div>
                <p className="leading-relaxed text-muted-foreground">{open.summary}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-success">Wins</div>
                  <ul className="space-y-1">{(open.wins ?? []).map((w: string, i: number) => <li key={i} className="text-muted-foreground">• {w}</li>)}</ul>
                </div>
                <div>
                  <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-danger">Losses</div>
                  <ul className="space-y-1">{(open.losses ?? []).map((w: string, i: number) => <li key={i} className="text-muted-foreground">• {w}</li>)}</ul>
                </div>
              </div>
              <div>
                <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-primary">Suggestions</div>
                <div className="flex flex-wrap gap-2">{(open.suggestions ?? []).map((w: string, i: number) => <Badge key={i} tone="primary">{w}</Badge>)}</div>
              </div>
              {open.strategy && (
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Upcoming Strategy</div>
                  <p className="leading-relaxed text-muted-foreground">{open.strategy}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
