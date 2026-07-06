"use client";

import { FlaskConical, Play, Quote, Search } from "lucide-react";
import { useState } from "react";
import {
  AetherEmpty, Chip, ErrorNote, FadeIn, GlassCard, LoadingAgents, SectionHeader, timeAgo,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Button, Input } from "@/components/ui";
import { type ResearchJob, useResearchJobs, useResearchSources, useRunResearch } from "@/lib/aether";
import { cn } from "@/lib/utils";

const statusTone: Record<string, "success" | "warning" | "danger" | "primary" | "default"> = {
  DONE: "success", COMPLETED: "success", SUCCESS: "success",
  RUNNING: "primary", PENDING: "warning", FAILED: "danger", ERROR: "danger",
};

function JobDetail({ job }: { job: ResearchJob }) {
  return (
    <FadeIn>
      <GlassCard glow className="p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-base font-semibold">"{job.query}"</h3>
          <Badge tone={statusTone[(job.status ?? "").toUpperCase()] ?? "default"}>{job.status ?? "—"}</Badge>
          <span className="text-xs text-muted-foreground">
            {(job.sources ?? []).join(" · ")} · {timeAgo(job.finished_at ?? job.created_at)}
          </span>
        </div>

        {job.summary && <p className="mt-4 text-sm leading-relaxed">{job.summary}</p>}

        {!!job.insights?.length && (
          <div className="mt-5">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Insights</div>
            <div className="overflow-x-auto rounded-xl border border-border/60">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/60 bg-muted/40 text-left text-muted-foreground">
                    <th className="px-3 py-2 font-medium">Insight</th>
                    <th className="px-3 py-2 font-medium">Evidence</th>
                    <th className="px-3 py-2 font-medium">Marketing use</th>
                  </tr>
                </thead>
                <tbody>
                  {job.insights.map((x, i) => (
                    <tr key={i} className="border-b border-border/40 align-top last:border-0">
                      <td className="px-3 py-2.5 font-medium">{x.insight}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">{x.evidence}</td>
                      <td className="px-3 py-2.5 text-violet-500">{x.marketing_use}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!!job.voice_of_customer?.length && (
          <div className="mt-5">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Voice of Customer</div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {job.voice_of_customer.map((v, i) => (
                <div key={i} className="rounded-xl border border-violet-500/25 bg-violet-500/5 p-4">
                  <Quote className="h-4 w-4 text-violet-500/60" />
                  <p className="mt-2 text-sm italic leading-relaxed">"{v.phrase}"</p>
                  <div className="mt-3 flex flex-wrap items-center gap-1.5">
                    {v.emotion && <Chip tone="danger">{v.emotion}</Chip>}
                    {v.use_as && <Badge tone="primary">use as: {v.use_as}</Badge>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </GlassCard>
    </FadeIn>
  );
}

export default function ResearchPage() {
  const sources = useResearchSources();
  const jobs = useResearchJobs();
  const run = useRunResearch();
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const allSources = sources.data?.sources ?? [];
  const list = jobs.data ?? [];
  const selected = list.find((j) => j.id === selectedId) ?? run.data ?? list[0] ?? null;

  const toggle = (s: string) => setPicked((p) => (p.includes(s) ? p.filter((x) => x !== s) : [...p, s]));

  const start = () => {
    if (!query.trim()) return;
    run.mutate(
      { query: query.trim(), sources: picked.length ? picked : allSources },
      { onSuccess: (j) => setSelectedId(j.id) },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Research Engine" subtitle="Mine forums, reviews and the open web for the exact words your customers use." />

      <GlassCard glow className="p-5">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[240px] flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && start()}
              placeholder="e.g. why do people abandon skincare routines?"
              className="pl-9"
            />
          </div>
          <Button disabled={run.isPending || !query.trim()} onClick={start} className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90">
            <Play className="h-4 w-4" /> {run.isPending ? "Researching…" : "Run research"}
          </Button>
        </div>
        {!!allSources.length && (
          <div className="mt-3 flex flex-wrap gap-2">
            {allSources.map((s) => (
              <button
                key={s}
                onClick={() => toggle(s)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors",
                  picked.includes(s) || !picked.length
                    ? "border-violet-500/60 bg-violet-500/15 text-violet-500"
                    : "border-border text-muted-foreground hover:text-foreground",
                )}
              >
                {s.replace(/_/g, " ")}
              </button>
            ))}
            <span className="self-center text-[11px] text-muted-foreground">{picked.length ? `${picked.length} selected` : "all sources"}</span>
          </div>
        )}
        <div className="mt-3"><ErrorNote error={run.error ?? undefined} /></div>
      </GlassCard>

      {run.isPending && <LoadingAgents label="Researching" sub="Reading threads, reviews and discussions — distilling insight from noise." />}

      {jobs.isLoading && <Loading />}
      {!jobs.isLoading && !list.length && !run.isPending && (
        <AetherEmpty
          icon={FlaskConical}
          title="No research yet"
          desc="Ask a question about your market. Aether scans Reddit, reviews and the web, then returns insights and verbatim customer language you can drop straight into ads."
          cta={<Button onClick={start} disabled={!query.trim()}><Play className="h-4 w-4" /> Start researching</Button>}
        />
      )}

      {selected && !run.isPending && <JobDetail job={selected} />}

      {list.length > 1 && (
        <div>
          <SectionHeader title="Past research" icon={FlaskConical} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((j, i) => (
              <FadeIn key={j.id} delay={0.02 * i}>
                <button className="block w-full text-left" onClick={() => setSelectedId(j.id)}>
                  <GlassCard
                    className={cn(
                      "h-full p-4 transition-all hover:-translate-y-0.5 hover:border-violet-500/40",
                      selected?.id === j.id && "border-violet-500/60 ring-1 ring-violet-500/30",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="truncate text-sm font-medium">"{j.query}"</div>
                      <Badge tone={statusTone[(j.status ?? "").toUpperCase()] ?? "default"}>{j.status}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {(j.sources ?? []).slice(0, 3).join(", ")} · {timeAgo(j.created_at)}
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
