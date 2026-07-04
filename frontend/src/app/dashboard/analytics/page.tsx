"use client";

import { Donut } from "@/components/dashboard/charts";
import { EmptyState, Loading, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useAnalytics } from "@/lib/hooks";
import { formatNumber } from "@/lib/utils";

export default function AnalyticsPage() {
  const { data, isLoading } = useAnalytics();
  if (isLoading) return <Loading />;
  const d = data ?? {};
  if (!d.sessions) return <><PageHeader title="Analytics" subtitle="Google Analytics 4" /><EmptyState title="No analytics yet" desc="Connect GA4 to see traffic." /></>;

  const sources = [
    { name: "Organic", value: d.traffic_sources?.organic ?? 0 },
    { name: "Paid", value: d.traffic_sources?.paid ?? 0 },
    { name: "Direct", value: d.traffic_sources?.direct ?? 0 },
    { name: "Referral", value: d.traffic_sources?.referral ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" subtitle="Google Analytics 4 · latest snapshot" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Visitors" value={formatNumber(d.visitors)} />
        <StatTile label="Sessions" value={formatNumber(d.sessions)} />
        <StatTile label="Bounce Rate" value={`${d.bounce_rate}%`} />
        <StatTile label="Avg Engagement" value={`${d.engagement_time}s`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Donut title="Traffic Sources (%)" data={sources} />
        <Card>
          <CardHeader><CardTitle>Devices & Browsers</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 text-xs text-muted-foreground">Devices</div>
              <div className="flex flex-wrap gap-2">
                {(d.devices ?? []).map((x: any) => (
                  <div key={x.device} className="rounded-lg border border-border px-3 py-1.5 text-sm">{x.device} · <span className="tabular font-medium">{x.share}%</span></div>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-2 text-xs text-muted-foreground">Browsers</div>
              <div className="flex flex-wrap gap-2">
                {(d.browsers ?? []).map((x: any) => (
                  <div key={x.browser} className="rounded-lg border border-border px-3 py-1.5 text-sm">{x.browser} · <span className="tabular font-medium">{x.share}%</span></div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Top Countries</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {(d.top_countries ?? []).map((x: any) => (
              <div key={x.country} className="flex justify-between text-sm"><span>{x.country}</span><span className="tabular text-muted-foreground">{formatNumber(x.sessions)}</span></div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Top Cities</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {(d.top_cities ?? []).map((x: any) => (
              <div key={x.city} className="flex justify-between text-sm"><span>{x.city}</span><span className="tabular text-muted-foreground">{formatNumber(x.sessions)}</span></div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
