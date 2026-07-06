"use client";

import {
  AlertOctagon, CalendarDays, Gauge, LineChart as LineChartIcon, ThumbsDown, ThumbsUp, TrendingUp,
} from "lucide-react";
import { useState } from "react";
import {
  PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer,
} from "recharts";
import {
  AetherEmpty, ErrorNote, FadeIn, GlassCard, LoadingAgents, PillTabs, SectionHeader,
} from "@/components/aether/shared";
import { Loading, ScoreRing, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button } from "@/components/ui";
import { type CampaignScore, useGenerateScores, usePerformanceAnalysis, useScores } from "@/lib/aether";
import { formatCompact } from "@/lib/utils";

const healthTone: Record<string, "success" | "warning" | "danger" | "default"> = {
  HEALTHY: "success", GOOD: "success", OK: "warning", WEAK: "warning", DEGRADED: "warning",
  BROKEN: "danger", CRITICAL: "danger", BAD: "danger",
};

const DIMS: { key: string; label: string }[] = [
  { key: "creative", label: "Creative" },
  { key: "audience", label: "Audience" },
  { key: "offer", label: "Offer" },
  { key: "landing_page", label: "Landing" },
  { key: "tracking", label: "Tracking" },
  { key: "brand", label: "Brand" },
  { key: "scaling", label: "Scaling" },
];

function ScoreRadar({ score }: { score: CampaignScore }) {
  const data = DIMS.map((d) => ({
    dim: d.label,
    value: Number((score.dimensions as any)?.[d.key] ?? 0),
  }));
  return (
    <GlassCard className="p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{score.campaign_id ?? "Account"}</div>
          <div className="text-xs text-muted-foreground">{score.date ? new Date(score.date).toLocaleDateString() : ""}</div>
        </div>
        <ScoreRing value={Math.round(score.overall ?? 0)} size={64} />
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis dataKey="dim" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.25} />
        </RadarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export default function PerformancePage() {
  const [days, setDays] = useState(14);
  const perf = usePerformanceAnalysis(days);
  const scores = useScores();
  const genScores = useGenerateScores();

  const brief = perf.data?.brief;
  const snap = perf.data?.snapshot;
  const hasData = !!brief?.headline || !!(snap?.campaigns ?? []).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance Analyst"
        subtitle="Aether reads your account like a senior media buyer — and tells you exactly what to do next."
        action={
          <PillTabs
            tabs={[{ key: "7", label: "7 days" }, { key: "14", label: "14 days" }, { key: "30", label: "30 days" }]}
            value={String(days)}
            onChange={(v) => setDays(Number(v))}
          />
        }
      />

      <ErrorNote error={perf.error ?? undefined} />
      {perf.isLoading && <LoadingAgents label="Analyzing performance" sub="Crunching campaign data and drafting your executive brief." />}

      {!perf.isLoading && !hasData && (
        <AetherEmpty
          icon={LineChartIcon}
          title="No performance data yet"
          desc="Once campaigns start spending, Aether delivers a daily executive brief — winners, losers, funnel diagnosis and a 7-day action plan."
        />
      )}

      {!perf.isLoading && hasData && (
        <>
          {/* Brief header */}
          {brief?.headline && (
            <FadeIn>
              <GlassCard glow className="p-5 sm:p-6">
                <div className="text-xs font-semibold uppercase tracking-wider text-violet-500">Executive brief</div>
                <h2 className="mt-2 text-xl font-semibold leading-snug">{brief.headline}</h2>
                {brief.binding_constraint && (
                  <div className="mt-3 flex items-start gap-2 rounded-xl border border-warning/40 bg-warning/10 p-3 text-sm">
                    <AlertOctagon className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-warning">Binding constraint</span>
                      <p className="mt-0.5 text-foreground/90">{brief.binding_constraint}</p>
                    </div>
                  </div>
                )}
              </GlassCard>
            </FadeIn>
          )}

          {/* Totals */}
          {snap?.totals && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
              <StatTile label="Spend" value={`$${formatCompact(snap.totals.spend ?? 0)}`} />
              <StatTile label="Revenue" value={`$${formatCompact(snap.totals.revenue ?? 0)}`} />
              <StatTile label="Orders" value={formatCompact(snap.totals.orders ?? 0)} />
              <StatTile label="Leads" value={formatCompact(snap.totals.leads ?? 0)} />
              <StatTile label="ROAS" value={`${(snap.recent_avg?.roas ?? 0).toFixed(2)}x`} hint={`prev ${(snap.prev_avg?.roas ?? 0).toFixed(2)}x`} />
              <StatTile label="CTR" value={`${(snap.recent_avg?.ctr ?? 0).toFixed(2)}%`} hint={`prev ${(snap.prev_avg?.ctr ?? 0).toFixed(2)}%`} />
              <StatTile label="CPA" value={`$${(snap.recent_avg?.cpa ?? 0).toFixed(2)}`} hint={`prev $${(snap.prev_avg?.cpa ?? 0).toFixed(2)}`} />
              <StatTile label="Conv. rate" value={`${(snap.recent_avg?.conversion_rate ?? 0).toFixed(2)}%`} hint={`AOV $${(snap.recent_avg?.aov ?? 0).toFixed(0)}`} />
            </div>
          )}

          {/* Winners / losers */}
          {(!!brief?.winners?.length || !!brief?.losers?.length) && (
            <div className="grid gap-4 lg:grid-cols-2">
              <GlassCard className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-success"><ThumbsUp className="h-4 w-4" /> Winners</div>
                <div className="mt-3 space-y-2.5">
                  {(brief?.winners ?? []).map((w, i) => (
                    <div key={i} className="rounded-lg border border-success/25 bg-success/5 p-3">
                      <div className="text-sm font-medium">{w.campaign}</div>
                      <div className="mt-0.5 text-xs text-muted-foreground">{w.why_winning}</div>
                      {w.action && <div className="mt-1.5 text-xs font-medium text-success">→ {w.action}</div>}
                    </div>
                  ))}
                  {!(brief?.winners ?? []).length && <div className="text-xs text-muted-foreground">No clear winners yet.</div>}
                </div>
              </GlassCard>
              <GlassCard className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-danger"><ThumbsDown className="h-4 w-4" /> Losers</div>
                <div className="mt-3 space-y-2.5">
                  {(brief?.losers ?? []).map((l, i) => (
                    <div key={i} className="rounded-lg border border-danger/25 bg-danger/5 p-3">
                      <div className="text-sm font-medium">{l.campaign}</div>
                      <div className="mt-0.5 text-xs text-muted-foreground">{l.why_failing}</div>
                      {l.action && <div className="mt-1.5 text-xs font-medium text-danger">→ {l.action}</div>}
                    </div>
                  ))}
                  {!(brief?.losers ?? []).length && <div className="text-xs text-muted-foreground">Nothing bleeding right now.</div>}
                </div>
              </GlassCard>
            </div>
          )}

          {/* Funnel diagnosis */}
          {!!brief?.funnel_diagnosis?.length && (
            <div>
              <SectionHeader title="Funnel Diagnosis" icon={Gauge} />
              <GlassCard className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="p-4 pb-2 font-medium">Stage</th>
                      <th className="p-4 pb-2 font-medium">Health</th>
                      <th className="p-4 pb-2 font-medium">Evidence</th>
                      <th className="p-4 pb-2 font-medium">Fix</th>
                    </tr>
                  </thead>
                  <tbody>
                    {brief.funnel_diagnosis.map((f, i) => (
                      <tr key={i} className="border-b border-border/60 last:border-0">
                        <td className="p-4 py-3 font-medium">{f.stage}</td>
                        <td className="p-4 py-3"><Badge tone={healthTone[(f.health ?? "").toUpperCase()] ?? "default"}>{f.health}</Badge></td>
                        <td className="p-4 py-3 text-xs text-muted-foreground">{f.evidence}</td>
                        <td className="p-4 py-3 text-xs">{f.fix}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </GlassCard>
            </div>
          )}

          {/* Risks + 7-day plan */}
          <div className="grid gap-4 lg:grid-cols-2">
            {!!brief?.risks?.length && (
              <GlassCard className="p-5">
                <div className="text-sm font-semibold">Risks</div>
                <ul className="mt-3 space-y-2 text-xs">
                  {brief.risks.map((r, i) => (
                    <li key={i} className="flex gap-2 rounded-lg border border-warning/25 bg-warning/5 p-2.5"><AlertOctagon className="h-3.5 w-3.5 shrink-0 text-warning" />{r}</li>
                  ))}
                </ul>
              </GlassCard>
            )}
            {!!brief?.seven_day_plan?.length && (
              <GlassCard className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold"><CalendarDays className="h-4 w-4 text-violet-500" /> 7-Day Plan</div>
                <ol className="mt-3 space-y-2">
                  {brief.seven_day_plan.map((d, i) => (
                    <li key={i} className="flex items-start gap-3 text-xs">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-violet-500/15 font-semibold text-violet-500">{String(d.day ?? i + 1).replace(/day\s*/i, "")}</span>
                      <span className="pt-1">{d.action}</span>
                    </li>
                  ))}
                </ol>
              </GlassCard>
            )}
          </div>

          {/* Campaign table */}
          {!!snap?.campaigns?.length && (
            <div>
              <SectionHeader title="Campaigns" icon={TrendingUp} />
              <GlassCard className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="p-4 pb-2 font-medium">Campaign</th>
                      <th className="p-4 pb-2 font-medium">Status</th>
                      <th className="p-4 pb-2 text-right font-medium">Spend</th>
                      <th className="p-4 pb-2 text-right font-medium">Revenue</th>
                      <th className="p-4 pb-2 text-right font-medium">ROAS</th>
                      <th className="p-4 pb-2 text-right font-medium">CTR</th>
                      <th className="p-4 pb-2 text-right font-medium">CPA</th>
                      <th className="p-4 pb-2 text-right font-medium">Freq</th>
                    </tr>
                  </thead>
                  <tbody className="tabular">
                    {snap.campaigns.map((c, i) => (
                      <tr key={i} className="border-b border-border/60 last:border-0">
                        <td className="p-4 py-3 font-medium">{c.name}</td>
                        <td className="p-4 py-3"><Badge tone={c.status === "ACTIVE" ? "success" : "default"}>{c.status ?? "—"}</Badge></td>
                        <td className="p-4 py-3 text-right">${formatCompact(c.spend ?? 0)}</td>
                        <td className="p-4 py-3 text-right">${formatCompact(c.revenue ?? 0)}</td>
                        <td className="p-4 py-3 text-right font-medium">{(c.roas ?? 0).toFixed(2)}x</td>
                        <td className="p-4 py-3 text-right">{(c.ctr ?? 0).toFixed(2)}%</td>
                        <td className="p-4 py-3 text-right">${(c.cpa ?? 0).toFixed(2)}</td>
                        <td className="p-4 py-3 text-right">{(c.frequency ?? 0).toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </GlassCard>
            </div>
          )}
        </>
      )}

      {/* Scorecards */}
      <div>
        <SectionHeader
          title="Scorecards"
          desc="Eight-dimension health scores per campaign — creative, audience, offer, landing, tracking, brand, scaling."
          icon={Gauge}
          action={
            <Button size="sm" variant="outline" disabled={genScores.isPending} onClick={() => genScores.mutate()}>
              <Gauge className="h-3.5 w-3.5" /> {genScores.isPending ? "Scoring…" : "Generate scores"}
            </Button>
          }
        />
        <ErrorNote error={genScores.error ?? undefined} />
        {genScores.isPending && <LoadingAgents label="Scoring campaigns" sub="Grading every dimension of every campaign." />}
        {scores.isLoading && <Loading />}
        {!scores.isLoading && !(scores.data ?? []).length && !genScores.isPending && (
          <div className="rounded-2xl border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
            No scorecards yet — hit "Generate scores" to grade every campaign across 8 dimensions.
          </div>
        )}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {(scores.data ?? []).map((s, i) => (
            <FadeIn key={s.id} delay={0.03 * i}><ScoreRadar score={s} /></FadeIn>
          ))}
        </div>
      </div>
    </div>
  );
}
