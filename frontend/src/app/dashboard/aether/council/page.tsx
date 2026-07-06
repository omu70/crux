"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, ChevronDown, Gavel, MessageSquareText, Play, Vote as VoteIcon } from "lucide-react";
import { useMemo, useState } from "react";
import {
  AetherEmpty, AgentAvatar, Chip, ErrorNote, FadeIn, GlassCard, LoadingAgents,
  SectionHeader, Select, Textarea, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Label } from "@/components/ui";
import { type CouncilRun, useCouncilRun, useCouncilRuns, useRosters, useRunCouncil } from "@/lib/aether";
import { cn } from "@/lib/utils";

const statusTone: Record<string, "success" | "warning" | "danger" | "primary" | "default"> = {
  DONE: "success", COMPLETED: "success", SUCCESS: "success",
  RUNNING: "primary", PENDING: "warning", FAILED: "danger", ERROR: "danger",
};
const verdictTone: Record<string, "success" | "warning" | "danger" | "default"> = {
  APPROVED: "success", PASS: "success", APPROVE: "success", SHIP: "success",
  REVISE: "warning", CONDITIONAL: "warning", REJECTED: "danger", FAIL: "danger", BLOCK: "danger",
};

function VotesViz({ run }: { run: CouncilRun }) {
  const votes = run.votes ?? [];
  const tally = useMemo(() => {
    const m = new Map<string, { count: number; conf: number }>();
    for (const v of votes) {
      const key = v.vote_for ?? "abstain";
      const cur = m.get(key) ?? { count: 0, conf: 0 };
      m.set(key, { count: cur.count + 1, conf: cur.conf + (v.confidence ?? 0) });
    }
    return [...m.entries()].sort((a, b) => b[1].count - a[1].count);
  }, [votes]);
  if (!votes.length) return null;
  const max = Math.max(...tally.map(([, t]) => t.count));

  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <VoteIcon className="h-3.5 w-3.5 text-violet-500" /> Council votes
      </div>
      <div className="space-y-2">
        {tally.map(([option, t]) => (
          <div key={option} className="rounded-lg border border-border/60 p-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium">{option}</span>
              <span className="tabular text-muted-foreground">{t.count} vote{t.count > 1 ? "s" : ""}</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500" style={{ width: `${(t.count / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 space-y-2">
        {votes.map((v, i) => (
          <div key={i} className="flex items-start gap-2.5 rounded-lg border border-border/50 p-2.5">
            <AgentAvatar name={v.voter ?? "?"} size={26} />
            <div className="min-w-0 flex-1 text-xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-medium">{v.voter}</span>
                <span className="text-muted-foreground">→</span>
                <Chip tone="violet">{v.vote_for}</Chip>
                {v.confidence != null && (
                  <span className="tabular text-muted-foreground">
                    {Math.round((v.confidence ?? 0) * ((v.confidence ?? 0) <= 1 ? 100 : 1))}% confident
                  </span>
                )}
              </div>
              {v.reason && <p className="mt-1 text-muted-foreground">{v.reason}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Transcript({ run }: { run: CouncilRun }) {
  const [open, setOpen] = useState(false);
  const messages = run.messages ?? [];
  if (!messages.length) return null;
  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-xl border border-border/60 px-4 py-3 text-sm font-medium transition-colors hover:bg-muted/40"
      >
        <span className="flex items-center gap-2">
          <MessageSquareText className="h-4 w-4 text-violet-500" /> Full debate transcript
          <span className="text-xs font-normal text-muted-foreground">({messages.length} messages)</span>
        </span>
        <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-3 max-h-[520px] space-y-3 overflow-y-auto rounded-xl border border-border/60 p-4">
              {messages.map((m, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <AgentAvatar name={m.agent ?? "?"} size={30} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-semibold">{m.agent}</span>
                      {m.action && <Chip className="px-2 py-0.5 text-[10px] uppercase">{m.action}</Chip>}
                    </div>
                    <div className="mt-1 whitespace-pre-wrap rounded-xl rounded-tl-sm border border-border/60 bg-background/50 px-3 py-2 text-xs leading-relaxed">
                      {m.content}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function RunDetail({ id }: { id: string }) {
  const { data: run, isLoading, error } = useCouncilRun(id);
  if (isLoading) return <Loading />;
  if (error) return <ErrorNote error={error} />;
  if (!run) return null;

  const d = run.decision?.decision;
  const review = run.decision?.review;

  return (
    <FadeIn>
      <GlassCard glow className="space-y-5 p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">{run.kind ?? "council"}</Badge>
          <Badge tone={statusTone[(run.status ?? "").toUpperCase()] ?? "default"}>{run.status ?? "—"}</Badge>
          {review?.verdict && (
            <Badge tone={verdictTone[review.verdict.toUpperCase()] ?? "default"}>
              <Gavel className="mr-1 h-3 w-3" /> Supervisor: {review.verdict}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">{timeAgo(run.created_at)}</span>
        </div>

        {d && (
          <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-violet-500">Decision</div>
            <p className="mt-1.5 text-sm font-medium leading-relaxed">{d.decision}</p>
            {d.why && (
              <>
                <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Why</div>
                <p className="mt-1 text-sm leading-relaxed text-foreground/90">{d.why}</p>
              </>
            )}
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {!!d.risks?.length && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-danger">Risks</div>
                  <ul className="mt-1 space-y-1 text-xs text-muted-foreground">{d.risks.map((r, i) => <li key={i}>• {r}</li>)}</ul>
                </div>
              )}
              {!!d.kill_criteria?.length && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-warning">Kill criteria</div>
                  <ul className="mt-1 space-y-1 text-xs text-muted-foreground">{d.kill_criteria.map((r, i) => <li key={i}>• {r}</li>)}</ul>
                </div>
              )}
              {!!d.first_48h_actions?.length && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-success">First 48h</div>
                  <ul className="mt-1 space-y-1 text-xs text-muted-foreground">{d.first_48h_actions.map((r, i) => <li key={i}>• {r}</li>)}</ul>
                </div>
              )}
            </div>
          </div>
        )}

        {review && (review.notes || !!review.defects?.length) && (
          <div className="rounded-xl border border-border/60 p-4 text-xs">
            <div className="font-semibold uppercase tracking-wider text-muted-foreground">Supervisor review</div>
            {review.notes && <p className="mt-1.5 leading-relaxed">{review.notes}</p>}
            {!!review.defects?.length && (
              <ul className="mt-2 space-y-1 text-danger/90">{review.defects.map((x, i) => <li key={i}>• {x}</li>)}</ul>
            )}
          </div>
        )}

        <VotesViz run={run} />
        <Transcript run={run} />

        <div className="flex flex-wrap items-center gap-4 border-t border-border/60 pt-3 text-[11px] tabular text-muted-foreground">
          <span>{(run.tokens_in ?? 0).toLocaleString()} tokens in</span>
          <span>{(run.tokens_out ?? 0).toLocaleString()} tokens out</span>
          <span className="font-medium text-foreground/80">${(run.cost_usd ?? 0).toFixed(4)} cost</span>
        </div>
      </GlassCard>
    </FadeIn>
  );
}

export default function CouncilPage() {
  const rosters = useRosters();
  const runs = useCouncilRuns();
  const council = useRunCouncil();
  const [kind, setKind] = useState("");
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const kinds = Object.keys(rosters.data ?? {});
  const activeKind = kind || kinds[0] || "";
  const roles = rosters.data?.[activeKind] ?? [];
  const list = runs.data ?? [];
  const detailId = selectedId ?? council.data?.id ?? list[0]?.id ?? null;

  const start = () => {
    if (!question.trim()) return;
    council.mutate(
      { kind: activeKind, question: question.trim(), context: context.trim() },
      { onSuccess: (r) => setSelectedId(r.id) },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader title="AI Council" subtitle="Eleven specialist agents debate, vote and rule on your hardest marketing decisions." />

      <GlassCard glow className="p-5 sm:p-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Council type</Label>
            <Select value={activeKind} onChange={(e) => setKind(e.target.value)} className="h-10 text-xs capitalize">
              {kinds.map((k) => <option key={k} value={k}>{k.replace(/_/g, " ")}</option>)}
              {!kinds.length && <option value="">loading…</option>}
            </Select>
            {!!roles.length && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {roles.map((r) => (
                  <span key={r} className="flex items-center gap-1.5 rounded-full border border-border/60 py-0.5 pl-0.5 pr-2 text-[10px] text-muted-foreground">
                    <AgentAvatar name={r} size={16} /> {r}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-1.5 lg:col-span-2">
            <Label className="text-xs">Question</Label>
            <Textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Should we double the budget on our top campaign, or diversify into new audiences?"
              className="min-h-[72px]"
            />
            <Label className="text-xs">Context <span className="font-normal text-muted-foreground">(optional)</span></Label>
            <Textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Any numbers, constraints or background the council should weigh…"
              className="min-h-[56px]"
            />
          </div>
        </div>
        <div className="mt-4">
          <Button
            disabled={council.isPending || !question.trim() || !activeKind}
            onClick={start}
            className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
          >
            <Play className="h-4 w-4" /> {council.isPending ? "Council in session…" : "Convene the council"}
          </Button>
        </div>
        <div className="mt-3"><ErrorNote error={council.error ?? undefined} /></div>
      </GlassCard>

      {council.isPending && (
        <LoadingAgents label="The council is deliberating" sub="Agents are debating, challenging each other and voting — big decisions take a minute or two." />
      )}

      {runs.isLoading && <Loading />}
      {!runs.isLoading && !list.length && !council.isPending && (
        <AetherEmpty
          icon={Bot}
          title="No council sessions yet"
          desc="Ask a strategic question and watch eleven AI specialists — strategist, buyer, analyst, contrarian and more — debate it, vote and hand down a ruling with kill criteria."
          cta={<Button onClick={start} disabled={!question.trim()}><Play className="h-4 w-4" /> Convene your first council</Button>}
        />
      )}

      {detailId && !council.isPending && <RunDetail id={detailId} />}

      {list.length > 1 && (
        <div>
          <SectionHeader title="Past sessions" icon={Bot} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((r, i) => (
              <FadeIn key={r.id} delay={0.02 * i}>
                <button className="block w-full text-left" onClick={() => setSelectedId(r.id)}>
                  <GlassCard
                    className={cn(
                      "h-full p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40",
                      detailId === r.id && "border-violet-500/60 ring-1 ring-violet-500/30",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <Badge tone="primary">{r.kind ?? "council"}</Badge>
                      <Badge tone={statusTone[(r.status ?? "").toUpperCase()] ?? "default"}>{r.status}</Badge>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                      {typeof r.input === "string" ? r.input : r.input?.question ?? "Council session"}
                    </p>
                    <div className="mt-2 text-[11px] tabular text-muted-foreground">
                      ${(r.cost_usd ?? 0).toFixed(3)} · {timeAgo(r.created_at)}
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
