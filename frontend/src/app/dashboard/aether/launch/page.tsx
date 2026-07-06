"use client";

import { Hammer, Rocket } from "lucide-react";
import { useState } from "react";
import { BlueprintView } from "@/components/aether/blueprint-view";
import {
  AetherEmpty, ErrorNote, FadeIn, GlassCard, LoadingAgents, SectionHeader, Select, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input, Label } from "@/components/ui";
import { useBlueprints, useBuildBlueprint, usePersonas } from "@/lib/aether";
import { cn } from "@/lib/utils";

const GOALS = ["SALES", "LEADS", "TRAFFIC", "AWARENESS", "APP_INSTALLS"];

export default function LaunchPage() {
  const blueprints = useBlueprints();
  const personas = usePersonas();
  const build = useBuildBlueprint();

  const [goal, setGoal] = useState("SALES");
  const [budget, setBudget] = useState(50);
  const [landing, setLanding] = useState("");
  const [personaIds, setPersonaIds] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const list = blueprints.data ?? [];
  const selected = list.find((b) => b.id === selectedId) ?? build.data ?? list[0] ?? null;

  const togglePersona = (id: string) =>
    setPersonaIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const run = () =>
    build.mutate(
      { goal, daily_budget: budget, persona_ids: personaIds, landing_url: landing.trim() },
      { onSuccess: (bp) => setSelectedId(bp.id) },
    );

  return (
    <div className="space-y-6">
      <PageHeader title="Campaign Builder" subtitle="Aether architects the full Meta campaign — structure, budgets, audiences, copy — ready to publish." />

      {/* Builder form */}
      <GlassCard glow className="p-5 sm:p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Goal</Label>
            <Select value={goal} onChange={(e) => setGoal(e.target.value)} className="h-10 text-xs">
              {GOALS.map((g) => <option key={g} value={g}>{g.replace(/_/g, " ")}</option>)}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Daily budget ($)</Label>
            <Input
              type="number" min={1}
              value={budget}
              onChange={(e) => setBudget(Math.max(1, Number(e.target.value) || 1))}
              className="h-10 text-xs"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label className="text-xs">Landing URL</Label>
            <Input value={landing} onChange={(e) => setLanding(e.target.value)} placeholder="https://yourbrand.com/offer" className="h-10 text-xs" />
          </div>
        </div>

        <div className="mt-4">
          <Label className="text-xs">Target personas</Label>
          <div className="mt-2 flex flex-wrap gap-2">
            {(personas.data ?? []).map((p) => (
              <button
                key={p.id}
                onClick={() => togglePersona(p.id)}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                  personaIds.includes(p.id)
                    ? "border-violet-500/60 bg-violet-500/15 text-violet-500"
                    : "border-border text-muted-foreground hover:border-violet-500/40 hover:text-foreground",
                )}
              >
                {p.name}
              </button>
            ))}
            {!(personas.data ?? []).length && (
              <span className="text-xs text-muted-foreground">
                No personas yet — generate some in the Audience module for sharper targeting.
              </span>
            )}
          </div>
        </div>

        <div className="mt-5">
          <Button
            disabled={build.isPending || !landing.trim()}
            onClick={run}
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
          >
            <Hammer className="h-4 w-4" /> {build.isPending ? "Architecting…" : "Build blueprint"}
          </Button>
        </div>
        <div className="mt-3"><ErrorNote error={build.error ?? undefined} /></div>
      </GlassCard>

      {build.isPending && <LoadingAgents label="Architecting your campaign" sub="Media buyer agents are designing structure, budget splits and ad copy." />}

      {blueprints.isLoading && <Loading />}
      {!blueprints.isLoading && !list.length && !build.isPending && !build.data && (
        <AetherEmpty
          icon={Rocket}
          title="No blueprints yet"
          desc="Give Aether a goal, budget and landing page — it returns a complete campaign blueprint with ad sets, budget splits, pixel mapping and a scaling plan, publishable in one click."
          cta={<Button onClick={run} disabled={!landing.trim()}><Hammer className="h-4 w-4" /> Build my first campaign</Button>}
        />
      )}

      {selected && !build.isPending && <BlueprintView key={selected.id} bp={selected} />}

      {list.length > 1 && (
        <div>
          <SectionHeader title="Blueprint history" icon={Rocket} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((b, i) => (
              <FadeIn key={b.id} delay={0.02 * i}>
                <button className="block w-full text-left" onClick={() => setSelectedId(b.id)}>
                  <GlassCard
                    className={cn(
                      "h-full p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40",
                      selected?.id === b.id && "border-violet-500/60 ring-1 ring-violet-500/30",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="truncate text-sm font-semibold">{b.name ?? "Blueprint"}</div>
                      <Badge tone="primary">{b.objective ?? "—"}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground tabular">
                      ${b.daily_budget ?? 0}/day · {(b.structure?.ad_sets ?? []).length} ad sets · {timeAgo(b.created_at)}
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
