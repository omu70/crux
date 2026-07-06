"use client";

import {
  Check, CircleDollarSign, Flame, Pause, RefreshCw, ScanLine,
  TrendingDown, TrendingUp, X,
} from "lucide-react";
import { useState } from "react";
import {
  AetherEmpty, ErrorNote, FadeIn, GlassCard, LoadingAgents, PillTabs, PrettyJson,
  ScoreBar, SeverityBadge, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button } from "@/components/ui";
import {
  type BudgetAction, type FatigueSignal, useApplyAction, useBudgetActions, useBudgetReview,
  useDismissAction, useFatigueSignals, useRefreshFatigue, useScanFatigue,
} from "@/lib/aether";

/* ── Fatigue tab ────────────────────────────────────────────────────────── */

function FatigueCard({ s, delay }: { s: FatigueSignal; delay: number }) {
  const refresh = useRefreshFatigue();
  const [showEvidence, setShowEvidence] = useState(false);
  return (
    <FadeIn delay={delay}>
      <GlassCard className="p-4">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={s.severity} />
          <span className="text-sm font-semibold capitalize">{(s.fatigue_type ?? "fatigue").replace(/_/g, " ")}</span>
          {s.resolved && <Badge tone="success">RESOLVED</Badge>}
          <span className="ml-auto text-[11px] text-muted-foreground">{timeAgo(s.created_at)}</span>
        </div>
        <div className="mt-1.5 text-xs text-muted-foreground">
          {s.entity_type ?? "entity"} · <span className="font-medium text-foreground/80">{s.entity_ref}</span>
        </div>
        {s.recommendation && (
          <p className="mt-2 rounded-lg border border-violet-500/25 bg-violet-500/5 p-2.5 text-xs leading-relaxed">
            {s.recommendation}
          </p>
        )}
        {s.evidence != null && (
          <div className="mt-2">
            <button onClick={() => setShowEvidence((v) => !v)} className="text-[11px] font-medium text-violet-500 hover:underline">
              {showEvidence ? "Hide evidence" : "Show evidence"}
            </button>
            {showEvidence && <PrettyJson data={s.evidence} className="mt-1.5" />}
          </div>
        )}
        <div className="mt-3 flex items-center justify-between gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={refresh.isPending}
            onClick={() => refresh.mutate(s.id)}
          >
            <RefreshCw className="h-3.5 w-3.5" /> {refresh.isPending ? "Generating…" : "Generate replacements"}
          </Button>
          {refresh.data && (
            <span className="text-xs text-success">
              {refresh.data.generated ?? refresh.data.asset_ids?.length ?? 0} new {refresh.data.kind ?? "assets"} created
            </span>
          )}
        </div>
        <ErrorNote error={refresh.error ?? undefined} />
      </GlassCard>
    </FadeIn>
  );
}

function FatigueTab() {
  const signals = useFatigueSignals();
  const scan = useScanFatigue();
  const list = signals.data ?? [];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">Aether watches frequency, CTR decay and comment sentiment for creative burnout.</p>
        <Button size="sm" disabled={scan.isPending} onClick={() => scan.mutate()} className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90">
          <ScanLine className="h-3.5 w-3.5" /> {scan.isPending ? "Scanning…" : "Scan for fatigue"}
        </Button>
      </div>
      <ErrorNote error={scan.error ?? undefined} />
      {scan.isPending && <LoadingAgents label="Scanning creatives" sub="Checking every live asset for fatigue signals." />}
      {signals.isLoading && <Loading />}
      {!signals.isLoading && !list.length && !scan.isPending && (
        <AetherEmpty
          icon={Flame}
          title="No fatigue signals"
          desc="Run a scan — Aether flags creatives that are burning out before your metrics tank, and can generate replacements instantly."
          cta={<Button onClick={() => scan.mutate()}><ScanLine className="h-4 w-4" /> Scan now</Button>}
        />
      )}
      <div className="grid gap-3 lg:grid-cols-2">
        {list.map((s, i) => <FatigueCard key={s.id} s={s} delay={0.03 * i} />)}
      </div>
    </div>
  );
}

/* ── Budget tab ─────────────────────────────────────────────────────────── */

function actionIcon(action?: string) {
  const a = (action ?? "").toUpperCase();
  if (a.includes("SCALE") || a.includes("INCREASE") || a.includes("UP")) return TrendingUp;
  if (a.includes("CUT") || a.includes("DECREASE") || a.includes("DOWN") || a.includes("REDUCE")) return TrendingDown;
  if (a.includes("PAUSE") || a.includes("STOP") || a.includes("KILL")) return Pause;
  return CircleDollarSign;
}

const actionStatusTone: Record<string, "primary" | "success" | "default"> = {
  PROPOSED: "primary", APPLIED: "success", DISMISSED: "default",
};

function ActionCard({ a, delay }: { a: BudgetAction; delay: number }) {
  const apply = useApplyAction();
  const dismiss = useDismissAction();
  const Icon = actionIcon(a.action);
  const conf = Math.round((a.confidence ?? 0) * ((a.confidence ?? 0) <= 1 ? 100 : 1));
  return (
    <FadeIn delay={delay}>
      <GlassCard className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/15 to-indigo-500/15 text-violet-500">
            <Icon className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold capitalize">{(a.action ?? "adjust").replace(/_/g, " ")}</span>
              {a.amount?.magnitude_pct != null && <Badge tone="primary">{a.amount.magnitude_pct > 0 ? "+" : ""}{a.amount.magnitude_pct}%</Badge>}
              <Badge tone={actionStatusTone[a.status] ?? "default"}>{a.status}</Badge>
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">{a.campaign_ref}</div>
          </div>
          <span className="text-[11px] text-muted-foreground">{timeAgo(a.created_at)}</span>
        </div>

        {a.reason && <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">{a.reason}</p>}
        {a.expected_impact && <p className="mt-1.5 text-xs"><span className="font-medium text-success">Expected impact:</span> {a.expected_impact}</p>}
        {a.amount?.trigger && <p className="mt-1 text-xs text-muted-foreground"><span className="font-medium">Trigger:</span> {a.amount.trigger}</p>}
        {a.amount?.rollback && <p className="mt-1 text-xs text-muted-foreground"><span className="font-medium">Rollback:</span> {a.amount.rollback}</p>}

        <div className="mt-3"><ScoreBar value={conf} label="Confidence" /></div>

        {a.status === "PROPOSED" && (
          <div className="mt-3 flex gap-2">
            <Button size="sm" disabled={apply.isPending || dismiss.isPending} onClick={() => apply.mutate(a.id)}>
              <Check className="h-3.5 w-3.5" /> {apply.isPending ? "Applying…" : "Apply"}
            </Button>
            <Button size="sm" variant="outline" disabled={apply.isPending || dismiss.isPending} onClick={() => dismiss.mutate(a.id)}>
              <X className="h-3.5 w-3.5" /> Dismiss
            </Button>
          </div>
        )}
        <ErrorNote error={apply.error ?? dismiss.error ?? undefined} />
      </GlassCard>
    </FadeIn>
  );
}

function BudgetTab() {
  const [status, setStatus] = useState("all");
  const actions = useBudgetActions(status === "all" ? undefined : status);
  const review = useBudgetReview();
  const list = actions.data ?? [];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PillTabs
          tabs={[{ key: "all", label: "All" }, { key: "PROPOSED", label: "Proposed" }, { key: "APPLIED", label: "Applied" }, { key: "DISMISSED", label: "Dismissed" }]}
          value={status}
          onChange={setStatus}
        />
        <Button size="sm" disabled={review.isPending} onClick={() => review.mutate()} className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90">
          <CircleDollarSign className="h-3.5 w-3.5" /> {review.isPending ? "Reviewing…" : "Run budget review"}
        </Button>
      </div>
      <ErrorNote error={review.error ?? undefined} />
      {review.isPending && <LoadingAgents label="Reviewing budgets" sub="Deciding where every dollar should move next." />}
      {actions.isLoading && <Loading />}
      {!actions.isLoading && !list.length && !review.isPending && (
        <AetherEmpty
          icon={CircleDollarSign}
          title="No budget actions"
          desc="Run a review — Aether proposes precise budget moves with confidence levels, triggers and rollback plans. You stay in control: apply or dismiss."
          cta={<Button onClick={() => review.mutate()}><CircleDollarSign className="h-4 w-4" /> Review budgets</Button>}
        />
      )}
      <div className="grid gap-3 lg:grid-cols-2">
        {list.map((a, i) => <ActionCard key={a.id} a={a} delay={0.03 * i} />)}
      </div>
    </div>
  );
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function OptimizerPage() {
  const [tab, setTab] = useState("fatigue");
  return (
    <div className="space-y-6">
      <PageHeader
        title="Optimizer"
        subtitle="Always-on guardian — catches creative fatigue and reallocates budget before performance slips."
        action={
          <PillTabs
            tabs={[{ key: "fatigue", label: "Creative Fatigue" }, { key: "budget", label: "Budget Actions" }]}
            value={tab}
            onChange={setTab}
          />
        }
      />
      {tab === "fatigue" ? <FatigueTab /> : <BudgetTab />}
    </div>
  );
}
