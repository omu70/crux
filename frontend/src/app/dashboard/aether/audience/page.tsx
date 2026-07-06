"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Crosshair, UserPlus, Users } from "lucide-react";
import { useState } from "react";
import {
  AetherEmpty, AgentAvatar, Chip, ErrorNote, FadeIn, GlassCard, LoadingAgents,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input } from "@/components/ui";
import { type Persona, useGeneratePersonas, usePersonas } from "@/lib/aether";
import { cn } from "@/lib/utils";

const awarenessTone: Record<string, "default" | "primary" | "success" | "warning" | "danger"> = {
  UNAWARE: "danger", "PROBLEM AWARE": "warning", PROBLEM_AWARE: "warning",
  "SOLUTION AWARE": "primary", SOLUTION_AWARE: "primary",
  "PRODUCT AWARE": "success", PRODUCT_AWARE: "success", "MOST AWARE": "success", MOST_AWARE: "success",
};

function SophisticationDots({ value }: { value?: number | string }) {
  const n = Math.max(0, Math.min(5, Math.round(Number(value) || 0)));
  if (!n) return <span className="text-xs text-muted-foreground">{value ? String(value) : "—"}</span>;
  return (
    <span className="inline-flex items-center gap-1" title={`Sophistication ${n}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={cn("h-1.5 w-1.5 rounded-full", i <= n ? "bg-violet-500" : "bg-muted")} />
      ))}
    </span>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</div>
      {children}
    </div>
  );
}

function PersonaDetail({ p }: { p: Persona }) {
  return (
    <div className="grid gap-5 border-t border-border/60 p-5 lg:grid-cols-2">
      <div className="space-y-4">
        {!!p.pains?.length && (
          <Block title="Pains"><div className="flex flex-wrap gap-1.5">{p.pains.map((x, i) => <Chip key={i} tone="danger">{x}</Chip>)}</div></Block>
        )}
        {!!p.fears?.length && (
          <Block title="Fears"><div className="flex flex-wrap gap-1.5">{p.fears.map((x, i) => <Chip key={i}>{x}</Chip>)}</div></Block>
        )}
        {!!p.dream_outcome?.length && (
          <Block title="Dream Outcome"><div className="flex flex-wrap gap-1.5">{p.dream_outcome.map((x, i) => <Chip key={i} tone="success">{x}</Chip>)}</div></Block>
        )}
        {!!p.objections?.length && (
          <Block title="Objections & Rebuttals">
            <div className="overflow-hidden rounded-lg border border-border/60">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/60 bg-muted/40 text-left text-muted-foreground">
                    <th className="px-3 py-2 font-medium">Objection</th>
                    <th className="px-3 py-2 font-medium">Rebuttal</th>
                  </tr>
                </thead>
                <tbody>
                  {p.objections.map((o, i) => (
                    <tr key={i} className="border-b border-border/40 last:border-0">
                      <td className="px-3 py-2 align-top text-danger/90">{o.objection}</td>
                      <td className="px-3 py-2 align-top">{o.rebuttal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Block>
        )}
        {!!p.jobs_to_be_done?.length && (
          <Block title="Jobs To Be Done">
            <div className="space-y-2">
              {p.jobs_to_be_done.map((j, i) => (
                <div key={i} className="rounded-lg border border-border/60 p-2.5 text-xs">
                  <div className="font-medium">{j.job}</div>
                  <div className="mt-0.5 text-muted-foreground">When: {j.context} → {j.outcome}</div>
                </div>
              ))}
            </div>
          </Block>
        )}
      </div>
      <div className="space-y-4">
        {p.identity && (
          <Block title="Identity">
            <div className="space-y-1.5 rounded-lg border border-border/60 p-3 text-xs">
              {p.identity.self_image && <div><span className="font-medium text-muted-foreground">Self-image: </span>{p.identity.self_image}</div>}
              {p.identity.aspiration && <div><span className="font-medium text-muted-foreground">Aspires to: </span>{p.identity.aspiration}</div>}
              {p.identity.tribe && <div><span className="font-medium text-muted-foreground">Tribe: </span>{p.identity.tribe}</div>}
            </div>
          </Block>
        )}
        {!!p.language?.length && (
          <Block title="Verbatim Language">
            <div className="flex flex-wrap gap-1.5">{p.language.map((x, i) => <Chip key={i} tone="violet">"{x}"</Chip>)}</div>
          </Block>
        )}
        {!!p.buying_triggers?.length && (
          <Block title="Buying Triggers"><div className="flex flex-wrap gap-1.5">{p.buying_triggers.map((x, i) => <Chip key={i}>{x}</Chip>)}</div></Block>
        )}
        {!!p.emotional_triggers?.length && (
          <Block title="Emotional Triggers"><div className="flex flex-wrap gap-1.5">{p.emotional_triggers.map((x, i) => <Chip key={i}>{x}</Chip>)}</div></Block>
        )}
        {!!p.lifestyle?.length && (
          <Block title="Lifestyle"><ul className="space-y-1 text-xs text-muted-foreground">{p.lifestyle.map((x, i) => <li key={i}>• {x}</li>)}</ul></Block>
        )}
        {p.behavior && (
          <Block title="Behavior">
            <div className="space-y-1.5 rounded-lg border border-border/60 p-3 text-xs">
              {!!p.behavior.channels?.length && <div><span className="font-medium text-muted-foreground">Channels: </span>{p.behavior.channels.join(", ")}</div>}
              {!!p.behavior.content?.length && <div><span className="font-medium text-muted-foreground">Content: </span>{p.behavior.content.join(", ")}</div>}
              {p.behavior.buying_habits && <div><span className="font-medium text-muted-foreground">Buying habits: </span>{p.behavior.buying_habits}</div>}
            </div>
          </Block>
        )}
        {p.targeting && (
          <Block title="Meta Targeting">
            <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-3 text-xs">
              {!!p.targeting.interests?.length && (
                <div className="flex flex-wrap gap-1.5">{p.targeting.interests.map((x, i) => <Chip key={i} tone="violet">{x}</Chip>)}</div>
              )}
              {!!p.targeting.behaviors?.length && (
                <div className="mt-2"><span className="font-medium text-muted-foreground">Behaviors: </span>{p.targeting.behaviors.join(", ")}</div>
              )}
              {p.targeting.age_range && <div className="mt-1.5"><span className="font-medium text-muted-foreground">Age: </span>{p.targeting.age_range}</div>}
              {p.targeting.notes && <div className="mt-1.5 text-muted-foreground">{p.targeting.notes}</div>}
            </div>
          </Block>
        )}
      </div>
    </div>
  );
}

export default function AudiencePage() {
  const personas = usePersonas();
  const generate = useGeneratePersonas();
  const [count, setCount] = useState(3);
  const [focus, setFocus] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  const list = personas.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Audience Intelligence" subtitle="Psychographic buyer personas — pains, dreams, objections and exact Meta targeting." />

      <GlassCard className="flex flex-wrap items-center gap-3 p-4">
        <Input
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          placeholder="Focus — e.g. high-LTV repeat buyers, gift shoppers…"
          className="h-10 max-w-md"
        />
        <Input
          type="number" min={1} max={8}
          value={count}
          onChange={(e) => setCount(Math.max(1, Math.min(8, Number(e.target.value) || 3)))}
          className="h-10 w-20"
        />
        <Button
          disabled={generate.isPending}
          onClick={() => generate.mutate({ count, focus: focus.trim() })}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
        >
          <UserPlus className="h-4 w-4" /> {generate.isPending ? "Generating…" : "Generate personas"}
        </Button>
      </GlassCard>
      <ErrorNote error={generate.error ?? undefined} />

      {generate.data?.market && (
        <GlassCard glow className="p-4 text-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-violet-500">Market read</span>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            {generate.data.market.market_sophistication != null && (
              <Badge tone="primary">Sophistication: {String(generate.data.market.market_sophistication)}</Badge>
            )}
            <span className="text-xs text-muted-foreground">{generate.data.market.market_notes}</span>
          </div>
        </GlassCard>
      )}

      {generate.isPending && <LoadingAgents label="Building personas" sub="Psychology, identity, objections, targeting — full dossiers take a minute." />}
      {personas.isLoading && <Loading />}

      {!personas.isLoading && !list.length && !generate.isPending && (
        <AetherEmpty
          icon={Users}
          title="No personas yet"
          desc="Aether turns your business profile and research into vivid buyer personas — complete with verbatim customer language and ready-to-use Meta targeting."
          cta={<Button onClick={() => generate.mutate({ count, focus: focus.trim() })}><UserPlus className="h-4 w-4" /> Generate personas</Button>}
        />
      )}

      <div className="space-y-3">
        {list.map((p, i) => {
          const open = openId === p.id;
          return (
            <FadeIn key={p.id} delay={0.04 * i}>
              <GlassCard className={cn("overflow-hidden transition-colors", open && "border-violet-500/50")}>
                <button className="flex w-full items-center gap-3 p-4 text-left" onClick={() => setOpenId(open ? null : p.id)}>
                  <AgentAvatar name={p.name} size={38} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold">{p.name}</span>
                      {p.awareness_level && (
                        <Badge tone={awarenessTone[p.awareness_level.toUpperCase()] ?? "default"}>{p.awareness_level}</Badge>
                      )}
                      {p.purchase_intent != null && (
                        <Chip tone="violet"><Crosshair className="mr-1 h-3 w-3" />intent: {String(p.purchase_intent)}</Chip>
                      )}
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="truncate">{p.segment}</span>
                      <SophisticationDots value={p.sophistication} />
                    </div>
                  </div>
                  <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
                </button>
                <AnimatePresence initial={false}>
                  {open && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <PersonaDetail p={p} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </GlassCard>
            </FadeIn>
          );
        })}
      </div>
    </div>
  );
}
