"use client";

import { useState } from "react";
import { AreaTrend, RangeSelector } from "@/components/dashboard/charts";
import { EmptyState, Loading, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useCampaigns, useTimeseries } from "@/lib/hooks";
import { formatCompact, formatCurrency } from "@/lib/utils";

const statusTone: Record<string, "success" | "warning" | "danger" | "primary" | "default"> = {
  ACTIVE: "success", PAUSED: "warning", REJECTED: "danger", LEARNING: "primary",
};

export default function AdsPage() {
  const [range, setRange] = useState("30d");
  const { data, isLoading } = useCampaigns();
  const ts = useTimeseries("ctr,cpa", range);

  if (isLoading) return <Loading />;
  const s = data?.summary ?? {};
  const campaigns = data?.campaigns ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Meta Ads" subtitle="Campaigns synced from the Meta Marketing API" action={<RangeSelector value={range} onChange={setRange} />} />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Active" value={s.active ?? 0} />
        <StatTile label="Learning" value={s.learning ?? 0} />
        <StatTile label="Paused" value={s.paused ?? 0} />
        <StatTile label="Rejected" value={s.rejected ?? 0} />
        <StatTile label="Total Spend" value={formatCurrency(s.total_spend ?? 0)} />
        <StatTile label="Total Revenue" value={formatCurrency(s.total_revenue ?? 0)} />
        <StatTile label="Winning" value={s.winning ?? "—"} />
        <StatTile label="Losing" value={s.losing ?? "—"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <AreaTrend title="CTR (%)" data={ts.data?.series ?? []} dataKey="ctr" color="hsl(var(--accent))" height={220} />
        <AreaTrend title="CPA ($)" data={ts.data?.series ?? []} dataKey="cpa" color="hsl(var(--danger))" height={220} />
      </div>

      <Card>
        <CardHeader><CardTitle>Campaigns</CardTitle></CardHeader>
        <CardContent>
          {campaigns.length === 0 ? <EmptyState title="No campaigns yet" /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Campaign</th>
                    <th className="pb-2 pr-4 font-medium">Status</th>
                    <th className="pb-2 pr-4 text-right font-medium">Spend</th>
                    <th className="pb-2 pr-4 text-right font-medium">Revenue</th>
                    <th className="pb-2 pr-4 text-right font-medium">ROAS</th>
                    <th className="pb-2 pr-4 text-right font-medium">CPA</th>
                    <th className="pb-2 text-right font-medium">CTR</th>
                  </tr>
                </thead>
                <tbody className="tabular">
                  {campaigns.map((c) => (
                    <tr key={c.id} className="border-b border-border/60 last:border-0">
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2 font-medium">
                          {c.name}
                          {c.is_winning && <Badge tone="success">Winning</Badge>}
                          {c.is_losing && <Badge tone="danger">Losing</Badge>}
                        </div>
                      </td>
                      <td className="py-3 pr-4"><Badge tone={statusTone[c.status]}>{c.status}</Badge></td>
                      <td className="py-3 pr-4 text-right">{formatCurrency(c.spend)}</td>
                      <td className="py-3 pr-4 text-right">{formatCurrency(c.revenue)}</td>
                      <td className="py-3 pr-4 text-right font-medium">{c.purchase_roas.toFixed(2)}x</td>
                      <td className="py-3 pr-4 text-right">{formatCurrency(c.cpa)}</td>
                      <td className="py-3 text-right">{c.ctr.toFixed(2)}%</td>
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
