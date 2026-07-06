"use client";

import { Layers, Megaphone, Send, Target, TrendingUp } from "lucide-react";
import { ErrorNote, FadeIn, GlassCard, KV, PrettyJson } from "@/components/aether/shared";
import { Badge, Button } from "@/components/ui";
import { type Blueprint, type PublishResult, usePublishBlueprint } from "@/lib/aether";

const statusTone: Record<string, "default" | "primary" | "success" | "warning"> = {
  DRAFT: "default", READY: "primary", PUBLISHED: "success", LIVE: "success", PENDING: "warning",
};

function asText(v: any): string | null {
  if (v == null) return null;
  return typeof v === "string" ? v : null;
}

export function BlueprintView({ bp }: { bp: Blueprint }) {
  const publish = usePublishBlueprint();
  const published = publish.data as PublishResult | undefined;
  const adSets = bp.structure?.ad_sets ?? [];

  return (
    <FadeIn>
      <GlassCard glow className="p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold">{bp.name ?? "Campaign Blueprint"}</h3>
              <Badge tone={statusTone[(bp.status ?? "").toUpperCase()] ?? "default"}>{bp.status ?? "DRAFT"}</Badge>
              {bp.objective && <Badge tone="primary">{bp.objective}</Badge>}
            </div>
            <div className="mt-1 text-xs text-muted-foreground tabular">
              Daily budget ${bp.daily_budget ?? 0} · {adSets.length} ad set{adSets.length === 1 ? "" : "s"}
            </div>
          </div>
          <Button
            disabled={publish.isPending}
            onClick={() => publish.mutate(bp.id)}
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
          >
            <Send className="h-4 w-4" /> {publish.isPending ? "Publishing…" : "Publish to Meta"}
          </Button>
        </div>
        <div className="mt-2"><ErrorNote error={publish.error ?? undefined} /></div>

        {published?.publish_result && (
          <div className="mt-3 rounded-xl border border-success/30 bg-success/10 p-4 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={published.publish_result.mode === "live" ? "success" : "warning"}>
                {(published.publish_result.mode ?? "mock").toUpperCase()} MODE
              </Badge>
              {published.publish_result.campaign_id && (
                <span className="text-xs tabular text-muted-foreground">campaign {published.publish_result.campaign_id}</span>
              )}
            </div>
            {published.publish_result.note && <p className="mt-1.5 text-xs text-muted-foreground">{published.publish_result.note}</p>}
          </div>
        )}

        {/* Structure tree */}
        <div className="mt-5">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Layers className="h-3.5 w-3.5 text-violet-500" /> Structure
          </div>
          <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Megaphone className="h-4 w-4 text-violet-500" />
              {typeof bp.structure?.campaign === "string"
                ? bp.structure.campaign
                : bp.structure?.campaign?.name ?? bp.name ?? "Campaign"}
            </div>
            <div className="mt-3 space-y-3 border-l border-violet-500/30 pl-4">
              {adSets.map((as_, i) => (
                <div key={i} className="rounded-lg border border-border/60 bg-background/40 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Target className="h-3.5 w-3.5 text-indigo-400" /> {as_.name ?? `Ad set ${i + 1}`}
                    </div>
                    <div className="flex items-center gap-2">
                      {as_.optimization_goal && <Badge>{as_.optimization_goal}</Badge>}
                      {as_.conversion_event && <Badge tone="primary">{as_.conversion_event}</Badge>}
                    </div>
                  </div>
                  {as_.audience && <div className="mt-1 text-xs text-muted-foreground">Audience: {as_.audience}</div>}
                  {!!as_.placements?.length && (
                    <div className="mt-1 text-xs text-muted-foreground">Placements: {as_.placements.join(", ")}</div>
                  )}
                  {/* budget split bar */}
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500"
                        style={{ width: `${Math.min(100, as_.budget_share_pct ?? 0)}%` }}
                      />
                    </div>
                    <span className="text-[11px] tabular text-muted-foreground">{as_.budget_share_pct ?? 0}% budget</span>
                  </div>
                  {!!as_.ads?.length && (
                    <div className="mt-3 space-y-2 border-l border-border/60 pl-3">
                      {as_.ads.map((ad, j) => (
                        <div key={j} className="rounded-lg border border-border/50 p-2.5 text-xs">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium">{ad.name ?? `Ad ${j + 1}`}</span>
                            {ad.cta_type && <Badge>{ad.cta_type}</Badge>}
                          </div>
                          {ad.headline && <div className="mt-1 font-medium text-violet-500">{ad.headline}</div>}
                          {ad.primary_text && <p className="mt-1 whitespace-pre-wrap text-muted-foreground">{ad.primary_text}</p>}
                          {ad.link && <div className="mt-1 truncate text-muted-foreground">{ad.link}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!adSets.length && <div className="text-xs text-muted-foreground">No ad sets in this blueprint.</div>}
            </div>
          </div>
        </div>

        {/* Strategy panels */}
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {bp.audience_strategy != null && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Audience strategy</div>
              {asText(bp.audience_strategy)
                ? <p className="text-sm leading-relaxed">{asText(bp.audience_strategy)}</p>
                : <KV data={bp.audience_strategy} />}
            </div>
          )}
          {bp.scaling_plan && (
            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <TrendingUp className="h-3.5 w-3.5 text-violet-500" /> Scaling plan
              </div>
              <div className="space-y-1.5 text-xs">
                {bp.scaling_plan.vertical && <div><span className="font-medium text-muted-foreground">Vertical: </span>{bp.scaling_plan.vertical}</div>}
                {bp.scaling_plan.horizontal && <div><span className="font-medium text-muted-foreground">Horizontal: </span>{bp.scaling_plan.horizontal}</div>}
                {!!bp.scaling_plan.triggers?.length && (
                  <ul className="mt-1.5 space-y-1">
                    {bp.scaling_plan.triggers.map((t, i) => (
                      <li key={i} className="rounded-md border border-warning/30 bg-warning/5 px-2 py-1 text-warning">{t}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
          {bp.pixel_mapping != null && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Pixel mapping</div>
              <div className="rounded-lg border border-border/60 p-3"><KV data={bp.pixel_mapping} /></div>
            </div>
          )}
          {bp.budget_plan != null && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Budget plan</div>
              {asText(bp.budget_plan)
                ? <p className="text-sm leading-relaxed">{asText(bp.budget_plan)}</p>
                : <div className="rounded-lg border border-border/60 p-3"><KV data={bp.budget_plan} /></div>}
            </div>
          )}
          {bp.creative_rotation != null && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Creative rotation</div>
              {asText(bp.creative_rotation)
                ? <p className="text-sm leading-relaxed">{asText(bp.creative_rotation)}</p>
                : <PrettyJson data={bp.creative_rotation} />}
            </div>
          )}
        </div>

        {bp.rationale && (
          <div className="mt-5 rounded-xl border border-violet-500/30 bg-violet-500/10 p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-violet-500">Why this structure</div>
            <p className="mt-1.5 text-sm leading-relaxed">{bp.rationale}</p>
          </div>
        )}
      </GlassCard>
    </FadeIn>
  );
}
