"use client";

import { Loading, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useSearchConsole, useSeo } from "@/lib/hooks";
import { formatNumber } from "@/lib/utils";

export default function SeoPage() {
  const gsc = useSearchConsole();
  const seo = useSeo();
  if (gsc.isLoading || seo.isLoading) return <Loading />;
  const g = gsc.data ?? {};
  const s = seo.data ?? {};

  return (
    <div className="space-y-6">
      <PageHeader title="Search & SEO" subtitle="Google Search Console + SEO health" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Clicks" value={formatNumber(g.clicks ?? 0)} />
        <StatTile label="Impressions" value={formatNumber(g.impressions ?? 0)} />
        <StatTile label="Avg Position" value={g.avg_position ?? "—"} />
        <StatTile label="CTR" value={`${g.ctr ?? 0}%`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Top Keywords</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {(g.top_keywords ?? []).map((k: any) => (
              <div key={k.keyword} className="flex items-center justify-between text-sm">
                <span>{k.keyword}</span>
                <span className="tabular text-muted-foreground">{formatNumber(k.clicks)} clicks · pos {k.position}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Top Pages</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            {(g.top_pages ?? []).map((p: any) => (
              <div key={p.page} className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate">{p.page}</span>
                <span className="tabular shrink-0 text-muted-foreground">{formatNumber(p.clicks)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Keyword Growth" value={`${s.keyword_growth ?? 0}%`} />
        <StatTile label="Backlinks" value={formatNumber(s.backlinks ?? 0)} />
        <StatTile label="Indexed Pages" value={formatNumber(s.indexed_pages ?? 0)} />
        <StatTile label="Technical Issues" value={s.technical_issues ?? 0} />
      </div>

      <Card>
        <CardHeader><CardTitle>Suggestions</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {(s.suggestions ?? []).map((x: string, i: number) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" /> {x}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
