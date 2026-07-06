"use client";

import { CheckCircle2, Eye, ScanEye } from "lucide-react";
import { useState } from "react";
import {
  AetherEmpty, ErrorNote, FadeIn, GlassCard, LoadingAgents, ScoreBar, SectionHeader, Select, timeAgo,
} from "@/components/aether/shared";
import { Loading, ScoreRing } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input } from "@/components/ui";
import { type VisualAnalysis, useAnalyzeVisual, useVisualHistory } from "@/lib/aether";

const KINDS = ["image", "video", "carousel", "thumbnail", "landing_page"];

const gauges: { key: keyof VisualAnalysis; label: string }[] = [
  { key: "creative_score", label: "Creative" },
  { key: "attention_score", label: "Attention" },
  { key: "scroll_stop_score", label: "Scroll-stop" },
  { key: "brand_score", label: "Brand" },
  { key: "emotion_score", label: "Emotion" },
];

function ResultView({ r }: { r: VisualAnalysis }) {
  return (
    <FadeIn>
      <GlassCard glow className="p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">{r.kind ?? "asset"}</Badge>
          <a href={r.asset_url} target="_blank" rel="noreferrer" className="truncate text-xs text-violet-500 hover:underline">{r.asset_url}</a>
          {r.provider && <span className="text-xs text-muted-foreground">· scored by {r.provider}</span>}
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-6">
          {gauges.map((g) => (
            <div key={String(g.key)} className="flex flex-col items-center">
              <ScoreRing value={Math.round(Number(r[g.key] ?? 0))} size={104} label={g.label} />
            </div>
          ))}
          <div className="flex flex-col items-center justify-center rounded-2xl border border-violet-500/30 bg-violet-500/10 px-6 py-4">
            <div className="text-3xl font-semibold tabular text-violet-500">
              {(Number(r.ctr_prediction ?? 0)).toFixed(2)}%
            </div>
            <div className="mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">Predicted CTR</div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {!!r.recommendations?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Recommendations</div>
              <ul className="space-y-2">
                {r.recommendations.map((x, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-lg border border-border/60 p-2.5 text-xs">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" /> {x}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!!r.observations?.length && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Observations</div>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                {r.observations.map((x, i) => <li key={i}>• {x}</li>)}
              </ul>
            </div>
          )}
        </div>
      </GlassCard>
    </FadeIn>
  );
}

export default function VisualAiPage() {
  const history = useVisualHistory();
  const analyze = useAnalyzeVisual();
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState("image");
  const [selected, setSelected] = useState<VisualAnalysis | null>(null);

  const result = selected ?? analyze.data ?? null;
  const list = history.data ?? [];

  const run = () => {
    if (!url.trim()) return;
    setSelected(null);
    analyze.mutate({ asset_url: url.trim(), kind });
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Visual AI" subtitle="Score any creative before a rupee is spent — attention, scroll-stop power, brand fit and predicted CTR." />

      <GlassCard className="flex flex-wrap items-center gap-3 p-4">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="https://cdn.yourbrand.com/creative.jpg"
          className="h-10 min-w-[240px] flex-1"
        />
        <Select value={kind} onChange={(e) => setKind(e.target.value)} className="h-10 w-36 text-xs capitalize">
          {KINDS.map((k) => <option key={k} value={k}>{k.replace(/_/g, " ")}</option>)}
        </Select>
        <Button
          disabled={analyze.isPending || !url.trim()}
          onClick={run}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
        >
          <ScanEye className="h-4 w-4" /> {analyze.isPending ? "Analyzing…" : "Analyze"}
        </Button>
      </GlassCard>
      <ErrorNote error={analyze.error ?? undefined} />

      {analyze.isPending && <LoadingAgents label="Scoring your creative" sub="Vision models are inspecting composition, hooks, emotion and brand signals." />}

      {result && !analyze.isPending && <ResultView r={result} />}

      {!result && !analyze.isPending && !history.isLoading && !list.length && (
        <AetherEmpty
          icon={Eye}
          title="No creatives analyzed yet"
          desc="Paste a URL to any ad image, video thumbnail or landing page. Aether's vision models return five scores plus a CTR prediction and concrete fixes."
          cta={<Button onClick={run} disabled={!url.trim()}><ScanEye className="h-4 w-4" /> Analyze a creative</Button>}
        />
      )}

      {history.isLoading && <Loading />}
      {!!list.length && (
        <div>
          <SectionHeader title="History" desc="Every analysis Aether has run for you." icon={Eye} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((h, i) => (
              <FadeIn key={h.id} delay={0.02 * i}>
                <button className="block w-full text-left" onClick={() => setSelected(h)}>
                  <GlassCard className="h-full p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40">
                    <div className="flex items-center justify-between gap-2">
                      <Badge tone="primary">{h.kind ?? "asset"}</Badge>
                      <span className="text-[11px] text-muted-foreground">{timeAgo(h.created_at)}</span>
                    </div>
                    <div className="mt-2 truncate text-xs text-muted-foreground">{h.asset_url}</div>
                    <div className="mt-3 space-y-1.5">
                      <ScoreBar value={Number(h.creative_score ?? 0)} label="Creative" />
                      <ScoreBar value={Number(h.attention_score ?? 0)} label="Attention" />
                    </div>
                    <div className="mt-2 text-xs">
                      Predicted CTR: <span className="font-semibold tabular text-violet-500">{Number(h.ctr_prediction ?? 0).toFixed(2)}%</span>
                    </div>
                  </GlassCard>
                </button>
              </FadeIn>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
