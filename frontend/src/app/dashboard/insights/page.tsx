"use client";

import { CalendarClock, CalendarDays, CalendarRange } from "lucide-react";
import { Loading } from "@/components/dashboard/common";
import { InsightCard } from "@/components/dashboard/insight-card";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useInsights, usePlan } from "@/lib/hooks";

const buckets = [
  { key: "today", label: "Today", icon: CalendarClock },
  { key: "week", label: "This Week", icon: CalendarDays },
  { key: "month", label: "This Month", icon: CalendarRange },
];
const prioTone: Record<string, "danger" | "warning" | "default"> = { HIGH: "danger", MEDIUM: "warning", LOW: "default" };

export default function InsightsPage() {
  const insights = useInsights();
  const plan = usePlan();

  return (
    <div className="space-y-6">
      <PageHeader title="AI Insights" subtitle="Intelligent, daily recommendations powered by Gemini" />

      {insights.isLoading ? <Loading /> : (
        <div className="grid gap-3 lg:grid-cols-2">
          {(insights.data ?? []).map((i, k) => <InsightCard key={i.id ?? k} insight={i} />)}
        </div>
      )}

      <div>
        <h2 className="mb-3 mt-2 text-lg font-semibold tracking-tight">Next Plan of Action</h2>
        {plan.isLoading ? <Loading /> : (
          <div className="grid gap-4 lg:grid-cols-3">
            {buckets.map((b) => (
              <Card key={b.key}>
                <CardHeader><CardTitle className="flex items-center gap-2"><b.icon className="h-4 w-4 text-primary" /> {b.label}</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {((plan.data?.[b.key] ?? []) as any[]).length === 0 && <p className="text-sm text-muted-foreground">Nothing scheduled.</p>}
                  {((plan.data?.[b.key] ?? []) as any[]).map((t: any, i: number) => (
                    <div key={i} className="rounded-lg border border-border p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="text-sm font-medium">{t.title}</div>
                        <Badge tone={prioTone[t.priority] ?? "default"}>{t.priority}</Badge>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{t.expected_result}</div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
