"use client";

import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Card, CardContent, Progress } from "@/components/ui";
import { useGoals } from "@/lib/hooks";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function GoalsPage() {
  const { data, isLoading } = useGoals();
  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6">
      <PageHeader title="Goal Tracker" subtitle="Monthly targets and live progress" />
      <div className="grid gap-4 sm:grid-cols-2">
        {(data ?? []).map((g: any) => {
          const money = g.unit === "$";
          const fmt = (n: number) => (money ? formatCurrency(n) : `${formatNumber(n)}${g.unit && g.unit !== "$" ? g.unit : ""}`);
          return (
            <Card key={g.id}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">{g.label}</div>
                  <div className="text-2xl font-semibold tabular text-primary">{g.progress}%</div>
                </div>
                <div className="mt-3"><Progress value={g.progress} /></div>
                <div className="mt-2 flex justify-between text-xs text-muted-foreground tabular">
                  <span>Current: {fmt(g.current)}</span>
                  <span>Target: {fmt(g.target)}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
