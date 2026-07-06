"use client";

import { PenTool, Wand2 } from "lucide-react";
import { useMemo, useState } from "react";
import {
  AetherEmpty, Chip, CopyButton, ErrorNote, FadeIn, GlassCard, LoadingAgents,
  PillTabs, ScoreBar, Select, contentToText, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input, Label } from "@/components/ui";
import {
  type CreativeAsset, type CreativeStatus, useCreativeOptions, useCreatives,
  useGenerateCreatives, usePersonas, useUpdateCreative,
} from "@/lib/aether";

const STATUSES: CreativeStatus[] = ["DRAFT", "APPROVED", "IN_USE", "RETIRED", "WINNER"];
const statusTone: Record<string, "default" | "primary" | "success" | "warning" | "danger"> = {
  DRAFT: "default", APPROVED: "primary", IN_USE: "warning", RETIRED: "danger", WINNER: "success",
};

function AssetCard({ asset, delay }: { asset: CreativeAsset; delay: number }) {
  const update = useUpdateCreative();
  const text = contentToText(asset.content);
  return (
    <FadeIn delay={delay}>
      <GlassCard className="flex h-full flex-col p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">{asset.kind}</Badge>
          {asset.framework && <Chip tone="violet">{asset.framework}</Chip>}
          <Badge tone={statusTone[asset.status] ?? "default"}>{asset.status}</Badge>
          <div className="ml-auto flex items-center gap-1.5">
            <CopyButton text={text} />
          </div>
        </div>

        <div className="mt-3 flex-1 whitespace-pre-wrap rounded-lg border border-border/60 bg-background/40 p-3 text-xs leading-relaxed">
          {text || <span className="text-muted-foreground">No content</span>}
        </div>

        {asset.meta?.angle && <div className="mt-2 text-xs text-muted-foreground"><span className="font-medium">Angle:</span> {asset.meta.angle}</div>}
        {asset.meta?.why_it_works && <div className="mt-1 text-xs text-muted-foreground"><span className="font-medium">Why it works:</span> {asset.meta.why_it_works}</div>}
        {asset.meta?.visual_direction && <div className="mt-1 text-xs text-muted-foreground"><span className="font-medium">Visual:</span> {asset.meta.visual_direction}</div>}

        <div className="mt-3">
          <ScoreBar value={asset.predicted_score ?? 0} label="Predicted performance" />
        </div>

        <div className="mt-3 flex items-center justify-between gap-2">
          <span className="text-[11px] text-muted-foreground">{timeAgo(asset.created_at)}</span>
          <Select
            className="h-8 w-32 px-2 text-xs"
            value={asset.status}
            disabled={update.isPending}
            onChange={(e) => update.mutate({ id: asset.id, status: e.target.value as CreativeStatus })}
          >
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
        <ErrorNote error={update.error ?? undefined} />
      </GlassCard>
    </FadeIn>
  );
}

export default function CreativeStudioPage() {
  const options = useCreativeOptions();
  const personas = usePersonas();
  const generate = useGenerateCreatives();

  const [kind, setKind] = useState("");
  const [framework, setFramework] = useState("");
  const [count, setCount] = useState(4);
  const [personaId, setPersonaId] = useState("");
  const [hint, setHint] = useState("");

  const [filterKind, setFilterKind] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  const assets = useCreatives({
    kind: filterKind === "all" ? undefined : filterKind,
    status: filterStatus === "all" ? undefined : filterStatus,
    limit: 60,
  });

  const kinds = options.data?.kinds ?? [];
  const frameworks = options.data?.frameworks ?? [];
  const activeKind = kind || kinds[0] || "";

  const kindTabs = useMemo(
    () => [{ key: "all", label: "All kinds" }, ...kinds.map((k) => ({ key: k, label: k.replace(/_/g, " ") }))],
    [kinds],
  );
  const statusTabs = [{ key: "all", label: "All statuses" }, ...STATUSES.map((s) => ({ key: s, label: s }))];

  const run = () =>
    generate.mutate({
      kind: activeKind,
      count,
      framework: framework || undefined,
      persona_id: personaId || undefined,
      product_hint: hint.trim(),
    });

  const list = assets.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Creative Studio" subtitle="Direct-response copy engineered by Aether — hooks, angles and full ads, scored before you spend." />

      {/* Controls */}
      <GlassCard glow className="p-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1.5">
            <Label className="text-xs">Kind</Label>
            <Select value={activeKind} onChange={(e) => setKind(e.target.value)} className="h-10 text-xs capitalize">
              {kinds.map((k) => <option key={k} value={k}>{k.replace(/_/g, " ")}</option>)}
              {!kinds.length && <option value="">loading…</option>}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Framework</Label>
            <Select value={framework} onChange={(e) => setFramework(e.target.value)} className="h-10 text-xs">
              <option value="">Auto-pick</option>
              {frameworks.map((f) => <option key={f} value={f}>{f}</option>)}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Persona</Label>
            <Select value={personaId} onChange={(e) => setPersonaId(e.target.value)} className="h-10 text-xs">
              <option value="">Any / general</option>
              {(personas.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Count — {count}</Label>
            <input
              type="range" min={1} max={10} value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="mt-3 w-full accent-violet-600"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Product hint</Label>
            <Input value={hint} onChange={(e) => setHint(e.target.value)} placeholder="e.g. Vitamin C serum" className="h-10 text-xs" />
          </div>
        </div>
        <div className="mt-4">
          <Button
            disabled={generate.isPending || !activeKind}
            onClick={run}
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
          >
            <Wand2 className="h-4 w-4" /> {generate.isPending ? "Generating…" : `Generate ${count} assets`}
          </Button>
        </div>
        <div className="mt-3"><ErrorNote error={generate.error ?? undefined} /></div>
      </GlassCard>

      {generate.isPending && <LoadingAgents label="Writing creatives" sub="Copywriter agents are drafting, critiquing and scoring your assets." />}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <PillTabs tabs={kindTabs} value={filterKind} onChange={setFilterKind} />
        <PillTabs tabs={statusTabs} value={filterStatus} onChange={setFilterStatus} />
      </div>

      {assets.isLoading && <Loading />}
      {!assets.isLoading && !list.length && !generate.isPending && (
        <AetherEmpty
          icon={PenTool}
          title="No creatives yet"
          desc="Pick a kind, a framework and a persona — Aether writes conversion-focused ad assets and predicts how each will perform."
          cta={<Button onClick={run} disabled={!activeKind}><Wand2 className="h-4 w-4" /> Generate your first batch</Button>}
        />
      )}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {list.map((a, i) => <AssetCard key={a.id} asset={a} delay={0.02 * i} />)}
      </div>
    </div>
  );
}
