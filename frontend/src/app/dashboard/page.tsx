"use client";

import { Bell, Bot, CircleDollarSign, Target, TriangleAlert, User2 } from "lucide-react";
import { useState } from "react";
import { AreaTrend, BarSeries, MultiLine, RangeSelector } from "@/components/dashboard/charts";
import { EmptyState, Loading, ScoreRing } from "@/components/dashboard/common";
import { InsightCard } from "@/components/dashboard/insight-card";
import { KpiGrid } from "@/components/dashboard/kpi-card";
import { Badge, Card, CardContent, CardHeader, CardTitle, Progress } from "@/components/ui";
import {
  useAlerts, useGoals, useInsights, usePerformanceScore, useSummary, useTimeseries,
} from "@/lib/hooks";
import { formatCurrency } from "@/lib/utils";

export default function OverviewPage() {
  const [range, setRange] = useState("30d");
  const summary = useSummary(range);
  const ts = useTimeseries("revenue,orders,roas,ad_spend", range);
  const insights = useInsights();
  const score = usePerformanceScore();
  const alerts = useAlerts();
  const goals = useGoals();

  if (summary.isLoading) return <Loading />;
  const s = summary.data!;
  const c = s.client;
  const series = ts.data?.series ?? [];

  return (
    <div className="space-y-6">
      {/* Greeting header */}
      <Card glass className="overflow-hidden">
        <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {s.greeting}, {c.company_name} <span className="align-middle">👋</span>
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {c.contact_name} · {c.current_month}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge tone="primary">{c.plan} plan</Badge>
              <Badge><CircleDollarSign className="mr-1 h-3 w-3" /> Budget {formatCurrency(c.monthly_budget, c.currency, true)}</Badge>
              {c.account_manager && (
                <Badge><User2 className="mr-1 h-3 w-3" /> {c.account_manager.name} · {c.account_manager.title}</Badge>
              )}
            </div>
          </div>
          <RangeSelector value={range} onChange={setRange} />
        </div>
      </Card>

      {/* KPI grid */}
      <KpiGrid cards={s.kpis} currency={c.currency} />

      {/* Charts */}
      <AreaTrend title="Revenue" data={series} dataKey="revenue" />
      <div className="grid gap-4 lg:grid-cols-2">
        <BarSeries title="Orders" data={series} dataKey="orders" color="hsl(var(--accent))" />
        <MultiLine
          title="ROAS vs Ad Spend"
          data={series}
          keys={[{ key: "roas", color: "hsl(var(--success))" }, { key: "ad_spend", color: "hsl(var(--primary))" }]}
        />
      </div>

      {/* Insights + performance score */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2"><Bot className="h-4 w-4 text-primary" /> AI Insights</CardTitle>
            <Badge tone="primary">Daily</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {insights.isLoading ? <Loading /> : (insights.data ?? []).slice(0, 4).map((i, k) => <InsightCard key={i.id ?? k} insight={i} />)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Performance Score</CardTitle></CardHeader>
          <CardContent>
            {score.isLoading ? <Loading /> : (
              <div className="flex flex-col items-center">
                <ScoreRing value={score.data?.overall ?? 0} label="/ 100" />
                <div className="mt-5 w-full space-y-2.5">
                  {Object.entries(score.data?.breakdown ?? {}).map(([k, v]) => (
                    <div key={k}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="text-muted-foreground">{k}</span>
                        <span className="font-medium tabular">{v as number}</span>
                      </div>
                      <Progress value={v as number} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Alerts + goals */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><TriangleAlert className="h-4 w-4 text-warning" /> Smart Alerts</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {alerts.isLoading ? <Loading /> :
              (alerts.data ?? []).length === 0 ? <EmptyState icon={Bell} title="All clear" desc="No active alerts right now." /> :
              (alerts.data ?? []).map((a: any) => (
                <div key={a.id} className="flex items-start gap-3 rounded-lg border border-border p-3">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-warning" />
                  <div>
                    <div className="text-sm font-medium">{a.title}</div>
                    <div className="text-xs text-muted-foreground">{a.message}</div>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-4 w-4 text-primary" /> Goal Tracker</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {goals.isLoading ? <Loading /> : (goals.data ?? []).map((g: any) => (
              <div key={g.id}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span>{g.label}</span>
                  <span className="tabular text-muted-foreground">
                    {g.unit === "$" ? formatCurrency(g.current, c.currency, true) : Math.round(g.current)}{g.unit && g.unit !== "$" ? g.unit : ""} / {g.unit === "$" ? formatCurrency(g.target, c.currency, true) : Math.round(g.target)}{g.unit && g.unit !== "$" ? g.unit : ""}
                  </span>
                </div>
                <Progress value={g.progress} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
