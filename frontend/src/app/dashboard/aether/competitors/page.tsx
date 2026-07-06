"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ExternalLink, Microscope, Radar, Swords, X } from "lucide-react";
import { useState } from "react";
import {
  AetherEmpty, Chip, ErrorNote, FadeIn, GlassCard, KV, LoadingAgents, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input } from "@/components/ui";
import { type Competitor, useAnalyzeCompetitor, useCompetitors, useDiscoverCompetitors } from "@/lib/aether";
import { cn } from "@/lib/utils";

const threatTone: Record<string, "danger" | "warning" | "success" | "default"> = {
  HIGH: "danger", CRITICAL: "danger", MEDIUM: "warning", LOW: "success",
};

function SwotBox({ title, items, className }: { title: string; items?: string[]; className?: string }) {
  return (
    <div className={cn("rounded-xl border p-4", className)}>
      <div className="text-xs font-semibold uppercase tracking-wider">{title}</div>
      <ul className="mt-2 space-y-1.5 text-xs leading-relaxed">
        {(items ?? []).map((s, i) => <li key={i}>• {s}</li>)}
        {!(items ?? []).length && <li className="text-muted-foreground">—</li>}
      </ul>
    </div>
  );
}

function CompetitorDetail({ c, onClose }: { c: Competitor; onClose: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}>
      <GlassCard glow className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">{c.name}</h3>
              <Badge tone={threatTone[(c.threat_level ?? "").toUpperCase()] ?? "default"}>
                {c.threat_level ?? "UNSCORED"} threat
              </Badge>
            </div>
            {c.website && (
              <a href={c.website} target="_blank" rel="noreferrer" className="mt-0.5 inline-flex items-center gap-1 text-xs text-violet-500 hover:underline">
                {c.website} <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted"><X className="h-4 w-4" /></button>
        </div>

        {c.positioning_gap && (
          <div className="mt-4 rounded-xl border border-violet-500/30 bg-violet-500/10 p-4 text-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-violet-500">Your positioning gap</span>
            <p className="mt-1 leading-relaxed">{c.positioning_gap}</p>
          </div>
        )}

        {/* SWOT quadrant */}
        <div className="mt-5">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">SWOT</div>
          <div className="grid gap-3 sm:grid-cols-2">
            <SwotBox title="Strengths" items={c.swot?.strengths} className="border-success/30 bg-success/5 text-success" />
            <SwotBox title="Weaknesses" items={c.swot?.weaknesses} className="border-danger/30 bg-danger/5 text-danger" />
            <SwotBox title="Opportunities" items={c.swot?.opportunities} className="border-violet-500/30 bg-violet-500/5 text-violet-500" />
            <SwotBox title="Threats" items={c.swot?.threats} className="border-warning/30 bg-warning/5 text-warning" />
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {!!c.creative_angles?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Creative angles</div>
              <div className="flex flex-wrap gap-2">{c.creative_angles.map((a, i) => <Chip key={i} tone="violet">{a}</Chip>)}</div>
            </div>
          )}
          {!!c.headlines?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Headlines they run</div>
              <ul className="space-y-1.5 text-sm">
                {c.headlines.map((h, i) => <li key={i} className="rounded-lg border border-border/60 px-3 py-1.5 text-xs italic">"{h}"</li>)}
              </ul>
            </div>
          )}
          {!!c.content_strategy?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Content strategy</div>
              <ul className="space-y-1 text-xs text-muted-foreground">{c.content_strategy.map((s, i) => <li key={i}>• {s}</li>)}</ul>
            </div>
          )}
          {c.reviews_summary && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Review intelligence</div>
              <div className="space-y-2 text-xs">
                {!!c.reviews_summary.positives?.length && (
                  <div><span className="font-medium text-success">Loved: </span>{c.reviews_summary.positives.join(" · ")}</div>
                )}
                {!!c.reviews_summary.negatives?.length && (
                  <div><span className="font-medium text-danger">Hated: </span>{c.reviews_summary.negatives.join(" · ")}</div>
                )}
                {!!c.reviews_summary.themes?.length && (
                  <div className="flex flex-wrap gap-1.5 pt-1">{c.reviews_summary.themes.map((t, i) => <Chip key={i}>{t}</Chip>)}</div>
                )}
              </div>
            </div>
          )}
          {c.pricing != null && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Pricing</div>
              <KV data={c.pricing} />
            </div>
          )}
          {!!c.funnels?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Funnels</div>
              <div className="space-y-1.5">{c.funnels.map((f, i) => <div key={i} className="rounded-lg border border-border/60 px-3 py-1.5 text-xs"><KV data={f} /></div>)}</div>
            </div>
          )}
        </div>
      </GlassCard>
    </motion.div>
  );
}

export default function CompetitorsPage() {
  const competitors = useCompetitors();
  const discover = useDiscoverCompetitors();
  const analyze = useAnalyzeCompetitor();
  const [hint, setHint] = useState("");
  const [count, setCount] = useState(5);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const list = competitors.data ?? [];
  const selected = list.find((c) => c.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <PageHeader title="Competitor Intelligence" subtitle="Discover rivals, dissect their playbook, find your gap." />

      <GlassCard className="flex flex-wrap items-center gap-3 p-4">
        <Input
          value={hint}
          onChange={(e) => setHint(e.target.value)}
          placeholder="Industry hint — e.g. premium DTC skincare in India"
          className="h-10 max-w-md"
        />
        <Input
          type="number" min={1} max={10}
          value={count}
          onChange={(e) => setCount(Math.max(1, Math.min(10, Number(e.target.value) || 5)))}
          className="h-10 w-20"
        />
        <Button
          disabled={discover.isPending}
          onClick={() => discover.mutate({ count, industry_hint: hint.trim() })}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
        >
          <Radar className="h-4 w-4" /> {discover.isPending ? "Discovering…" : "Discover competitors"}
        </Button>
      </GlassCard>
      <ErrorNote error={discover.error ?? analyze.error ?? undefined} />

      {discover.isPending && <LoadingAgents label="Scouting the battlefield" sub="Aether is hunting for the competitors most likely to steal your customers." />}
      {competitors.isLoading && <Loading />}

      {!competitors.isLoading && !list.length && !discover.isPending && (
        <AetherEmpty
          icon={Swords}
          title="No competitors tracked yet"
          desc="Aether discovers your closest rivals, then reverse-engineers their offers, ads, funnels and reviews so you can outflank them."
          cta={<Button onClick={() => discover.mutate({ count, industry_hint: hint.trim() })}><Radar className="h-4 w-4" /> Discover competitors</Button>}
        />
      )}

      {!!list.length && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((c, i) => (
            <FadeIn key={c.id} delay={0.03 * i}>
              <GlassCard
                role="button"
                tabIndex={0}
                onClick={() => setSelectedId(c.id === selectedId ? null : c.id)}
                className={cn(
                  "h-full cursor-pointer p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40",
                  selectedId === c.id && "border-violet-500/60 ring-1 ring-violet-500/30",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="text-sm font-semibold">{c.name}</div>
                  <Badge tone={threatTone[(c.threat_level ?? "").toUpperCase()] ?? "default"}>{c.threat_level ?? "NEW"}</Badge>
                </div>
                {c.website && <div className="mt-0.5 truncate text-xs text-muted-foreground">{c.website}</div>}
                <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                  {c.positioning_gap ?? "Not analyzed yet — run a deep analysis to expose their playbook."}
                </p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">
                    {c.last_analyzed_at ? `analyzed ${timeAgo(c.last_analyzed_at)}` : "never analyzed"}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={analyze.isPending}
                    onClick={(e) => {
                      e.stopPropagation();
                      analyze.mutate(c.id, { onSuccess: () => setSelectedId(c.id) });
                    }}
                  >
                    <Microscope className="h-3.5 w-3.5" />
                    {analyze.isPending && analyze.variables === c.id ? "Analyzing…" : "Analyze"}
                  </Button>
                </div>
              </GlassCard>
            </FadeIn>
          ))}
        </div>
      )}

      {analyze.isPending && <LoadingAgents label="Dissecting competitor" sub="Reading their site, ads, reviews and funnels — building the full dossier." />}

      <AnimatePresence>
        {selected && !analyze.isPending && (
          <CompetitorDetail key={selected.id} c={selected} onClose={() => setSelectedId(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
