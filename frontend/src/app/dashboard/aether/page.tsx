"use client";

import {
  Bot, Brain, CreditCard, Eye, LineChart, PenTool, Rocket, Search, SlidersHorizontal,
  Sparkles, Sunrise, Swords, Users, Wallet, Zap,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/dashboard/shell";
import {
  ErrorNote, FadeIn, GlassCard, SectionHeader, timeAgo,
} from "@/components/aether/shared";
import { Badge, Button, Skeleton } from "@/components/ui";
import {
  useAutomationRuns, useBillingPlans, useCheckout, useMorningReport,
  usePerformanceAnalysis, useSubscription, useUsageSummary,
} from "@/lib/aether";

const modules = [
  { href: "/dashboard/aether/business", icon: Brain, name: "Business Intel", desc: "Deep-scan your brand, offers & funnel" },
  { href: "/dashboard/aether/competitors", icon: Swords, name: "Competitor Spy", desc: "Discover & dissect rivals with SWOT" },
  { href: "/dashboard/aether/audience", icon: Users, name: "Audience Personas", desc: "Psychographic buyer personas" },
  { href: "/dashboard/aether/studio", icon: PenTool, name: "Creative Studio", desc: "AI ad copy, hooks & scripts at scale" },
  { href: "/dashboard/aether/visual", icon: Eye, name: "Visual AI", desc: "Score creatives before you spend" },
  { href: "/dashboard/aether/launch", icon: Rocket, name: "Campaign Builder", desc: "Full Meta blueprints, one click" },
  { href: "/dashboard/aether/performance", icon: LineChart, name: "Performance Analyst", desc: "Winners, losers & 7-day plans" },
  { href: "/dashboard/aether/optimizer", icon: SlidersHorizontal, name: "Optimizer", desc: "Fatigue alerts & budget moves" },
  { href: "/dashboard/aether/research", icon: Search, name: "Research Engine", desc: "Voice-of-customer mining" },
  { href: "/dashboard/aether/council", icon: Bot, name: "AI Council", desc: "11 agents debate your big calls" },
];

const runTone: Record<string, "success" | "warning" | "danger" | "primary" | "default"> = {
  SUCCESS: "success", DONE: "success", COMPLETED: "success", RUNNING: "primary",
  PENDING: "warning", FAILED: "danger", ERROR: "danger",
};

export default function AetherCommandCenter() {
  const sub = useSubscription();
  const plans = useBillingPlans();
  const usage = useUsageSummary();
  const runs = useAutomationRuns();
  const perf = usePerformanceAnalysis(14);
  const morning = useMorningReport();
  const checkout = useCheckout();

  const planKeys = Object.keys(plans.data ?? {});
  const currentPlan = sub.data?.plan;

  return (
    <div className="space-y-6">
      <PageHeader title="Aether AI" subtitle="Command Center" />

      {/* Hero */}
      <FadeIn>
        <GlassCard glow className="relative overflow-hidden p-6 sm:p-8">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-gradient-to-br from-violet-600/20 to-indigo-500/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-28 -left-16 h-56 w-56 rounded-full bg-indigo-500/10 blur-3xl" />
          <div className="relative">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-600 dark:text-violet-400">
              <Sparkles className="h-3.5 w-3.5" /> Aether AI Suite
            </div>
            <h2 className="mt-4 text-2xl font-semibold tracking-tight sm:text-3xl">
              The AI media buyer that{" "}
              <span className="bg-gradient-to-r from-violet-500 to-indigo-400 bg-clip-text text-transparent">never sleeps</span>
            </h2>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">
              Ten intelligence modules and an eleven-agent council working around the clock — researching, creating,
              launching and optimizing your paid media while you focus on the business.
            </p>
          </div>
        </GlassCard>
      </FadeIn>

      {/* Plan / usage / brief row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <FadeIn delay={0.05}>
          <GlassCard id="billing" className="h-full p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold"><CreditCard className="h-4 w-4 text-violet-500" /> Subscription</div>
              {sub.data?.status && <Badge tone={sub.data.status === "ACTIVE" ? "success" : "warning"}>{sub.data.status}</Badge>}
            </div>
            {sub.isLoading ? (
              <Skeleton className="mt-4 h-16" />
            ) : (
              <>
                <div className="mt-3 text-xl font-semibold">{sub.data?.plan_name ?? sub.data?.plan ?? "Free"}</div>
                <div className="text-xs text-muted-foreground">
                  ${sub.data?.price_usd ?? 0}/mo
                  {sub.data?.current_period_end && <> · renews {new Date(sub.data.current_period_end).toLocaleDateString()}</>}
                </div>
                {planKeys.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {planKeys.map((k) => (
                      <Button
                        key={k}
                        size="sm"
                        variant={k === currentPlan ? "secondary" : "outline"}
                        disabled={k === currentPlan || checkout.isPending}
                        onClick={() =>
                          checkout.mutate({ plan: k }, { onSuccess: (r) => { if (r.url) window.open(r.url, "_blank"); } })
                        }
                      >
                        {plans.data?.[k]?.name ?? k}
                        <span className="text-muted-foreground">${plans.data?.[k]?.price_usd}</span>
                      </Button>
                    ))}
                  </div>
                )}
                <ErrorNote error={checkout.error ?? undefined} />
              </>
            )}
          </GlassCard>
        </FadeIn>

        <FadeIn delay={0.1}>
          <GlassCard className="h-full p-5">
            <div className="flex items-center gap-2 text-sm font-semibold"><Wallet className="h-4 w-4 text-violet-500" /> AI Usage · {usage.data?.days ?? 30}d</div>
            {usage.isLoading ? (
              <Skeleton className="mt-4 h-16" />
            ) : (
              <>
                <div className="mt-3 text-xl font-semibold tabular">${(usage.data?.total_cost_usd ?? 0).toFixed(2)}</div>
                <div className="text-xs text-muted-foreground">total model spend</div>
                <div className="mt-3 space-y-1.5">
                  {(usage.data?.by_provider ?? []).slice(0, 4).map((p, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{p.provider} · {p.kind}</span>
                      <span className="tabular font-medium">${(p.cost_usd ?? 0).toFixed(3)}</span>
                    </div>
                  ))}
                  {!(usage.data?.by_provider ?? []).length && <div className="text-xs text-muted-foreground">No usage recorded yet.</div>}
                </div>
              </>
            )}
          </GlassCard>
        </FadeIn>

        <FadeIn delay={0.15}>
          <GlassCard className="h-full p-5">
            <div className="flex items-center gap-2 text-sm font-semibold"><Zap className="h-4 w-4 text-violet-500" /> Latest Performance Brief</div>
            {perf.isLoading ? (
              <Skeleton className="mt-4 h-16" />
            ) : perf.data?.brief?.headline ? (
              <>
                <p className="mt-3 text-sm leading-relaxed">{perf.data.brief.headline}</p>
                {perf.data.brief.binding_constraint && (
                  <p className="mt-2 text-xs text-warning">Constraint: {perf.data.brief.binding_constraint}</p>
                )}
                <Link href="/dashboard/aether/performance" className="mt-3 inline-block text-xs font-medium text-violet-500 hover:underline">
                  Open full analysis →
                </Link>
              </>
            ) : (
              <p className="mt-3 text-xs text-muted-foreground">
                No brief yet. Run the <Link href="/dashboard/aether/performance" className="text-violet-500 hover:underline">Performance Analyst</Link> to get your first one.
              </p>
            )}
          </GlassCard>
        </FadeIn>
      </div>

      {/* Modules grid */}
      <div>
        <SectionHeader title="Modules" desc="Every weapon in the Aether arsenal — one click away." icon={Sparkles} />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {modules.map((m, i) => (
            <FadeIn key={m.href} delay={0.03 * i}>
              <Link href={m.href} className="block h-full">
                <GlassCard className="group h-full p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/15 to-indigo-500/15 text-violet-500 transition-colors group-hover:from-violet-500/25 group-hover:to-indigo-500/25 dark:text-violet-400">
                    <m.icon className="h-[18px] w-[18px]" />
                  </div>
                  <div className="mt-3 text-sm font-semibold">{m.name}</div>
                  <div className="mt-1 text-xs leading-relaxed text-muted-foreground">{m.desc}</div>
                </GlassCard>
              </Link>
            </FadeIn>
          ))}
        </div>
      </div>

      {/* Automations */}
      <div>
        <SectionHeader
          title="Automations"
          desc="Scheduled jobs Aether runs while you sleep."
          icon={Sunrise}
          action={
            <Button size="sm" variant="outline" disabled={morning.isPending} onClick={() => morning.mutate()}>
              <Sunrise className="h-3.5 w-3.5" />
              {morning.isPending ? "Generating…" : "Run morning report"}
            </Button>
          }
        />
        <ErrorNote error={morning.error ?? undefined} />
        <GlassCard className="mt-2 divide-y divide-border/60">
          {runs.isLoading && <div className="p-4"><Skeleton className="h-12" /></div>}
          {!runs.isLoading && !(runs.data ?? []).length && (
            <div className="p-5 text-center text-xs text-muted-foreground">
              No automation runs yet — trigger the morning report to see Aether's daily digest.
            </div>
          )}
          {(runs.data ?? []).slice(0, 6).map((r) => (
            <div key={r.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <div className="truncate text-sm font-medium capitalize">{(r.kind ?? "run").replace(/[_-]/g, " ")}</div>
                <div className="text-xs text-muted-foreground">{timeAgo(r.created_at)}</div>
              </div>
              <Badge tone={runTone[(r.status ?? "").toUpperCase()] ?? "default"}>{r.status ?? "—"}</Badge>
            </div>
          ))}
        </GlassCard>
      </div>
    </div>
  );
}
