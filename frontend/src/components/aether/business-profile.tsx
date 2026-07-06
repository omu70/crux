"use client";

import {
  AlertTriangle, ArrowDown, BadgeDollarSign, Compass, Fingerprint, Heart, Map,
  Palette, ShieldCheck, Sparkles, Users2,
} from "lucide-react";
import { Chip, FadeIn, GlassCard, SectionHeader, timeAgo } from "@/components/aether/shared";
import { Badge } from "@/components/ui";
import type { BusinessProfile } from "@/lib/aether";

function TextCard({ icon: Icon, title, text, delay = 0 }: { icon: any; title: string; text?: string; delay?: number }) {
  if (!text) return null;
  return (
    <FadeIn delay={delay}>
      <GlassCard className="h-full p-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Icon className="h-3.5 w-3.5 text-violet-500" /> {title}
        </div>
        <p className="mt-2 text-sm leading-relaxed">{text}</p>
      </GlassCard>
    </FadeIn>
  );
}

export function BusinessProfileView({ profile }: { profile: BusinessProfile }) {
  const p = profile;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="primary">{p.status ?? "READY"}</Badge>
        {p.website_url && <span className="text-xs text-muted-foreground">{p.website_url}</span>}
        <span className="text-xs text-muted-foreground">· updated {timeAgo(p.updated_at ?? p.created_at)}</span>
      </div>

      {/* Narrative cards */}
      <div className="grid gap-4 lg:grid-cols-2">
        <TextCard icon={Sparkles} title="Summary" text={p.summary} />
        <TextCard icon={Fingerprint} title="Unique Selling Proposition" text={p.usp} delay={0.05} />
        <TextCard icon={Compass} title="Positioning" text={p.positioning} delay={0.1} />
        <div className="grid gap-4 sm:grid-cols-2">
          <TextCard icon={Heart} title="Brand Voice" text={p.brand_voice} delay={0.12} />
          <TextCard icon={Palette} title="Visual Style" text={p.visual_style} delay={0.15} />
        </div>
      </div>

      {/* Offers */}
      {!!p.offers?.length && (
        <div>
          <SectionHeader title="Offers" icon={BadgeDollarSign} />
          <GlassCard className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="p-4 pb-2 font-medium">Offer</th>
                  <th className="p-4 pb-2 font-medium">Price</th>
                  <th className="p-4 pb-2 font-medium">Type</th>
                  <th className="p-4 pb-2 font-medium">Angle</th>
                </tr>
              </thead>
              <tbody>
                {p.offers.map((o, i) => (
                  <tr key={i} className="border-b border-border/60 last:border-0">
                    <td className="p-4 py-3 font-medium">{o.name}</td>
                    <td className="p-4 py-3 tabular">{o.price ?? "—"}</td>
                    <td className="p-4 py-3"><Badge>{o.type ?? "—"}</Badge></td>
                    <td className="p-4 py-3 text-muted-foreground">{o.angle}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
          {p.price_analysis && (
            <GlassCard className="mt-3 p-4">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Price analysis</span>
                {p.price_analysis.tier && <Badge tone="primary">{p.price_analysis.tier}</Badge>}
                {p.price_analysis.vs_market && <span className="text-xs text-muted-foreground">{p.price_analysis.vs_market}</span>}
              </div>
              {!!p.price_analysis.opportunities?.length && (
                <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                  {p.price_analysis.opportunities.map((o, i) => (
                    <li key={i} className="flex gap-2"><span className="text-violet-500">→</span>{o}</li>
                  ))}
                </ul>
              )}
            </GlassCard>
          )}
        </div>
      )}

      {/* Strengths / weaknesses */}
      {(!!p.strengths?.length || !!p.weaknesses?.length) && (
        <div className="grid gap-4 lg:grid-cols-2">
          <GlassCard className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-success"><ShieldCheck className="h-4 w-4" /> Strengths</div>
            <ul className="mt-3 space-y-2 text-sm">
              {(p.strengths ?? []).map((s, i) => (
                <li key={i} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-success" />{s}</li>
              ))}
            </ul>
          </GlassCard>
          <GlassCard className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-danger"><AlertTriangle className="h-4 w-4" /> Weaknesses</div>
            <ul className="mt-3 space-y-2 text-sm">
              {(p.weaknesses ?? []).map((s, i) => (
                <li key={i} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-danger" />{s}</li>
              ))}
            </ul>
          </GlassCard>
        </div>
      )}

      {/* Customer journey timeline */}
      {!!p.customer_journey?.length && (
        <div>
          <SectionHeader title="Customer Journey" icon={Map} />
          <GlassCard className="p-5">
            <ol className="relative space-y-5 border-l border-violet-500/30 pl-5">
              {p.customer_journey.map((j, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[27px] top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full border border-violet-500/50 bg-background">
                    <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                  </span>
                  <div className="text-sm font-semibold">{j.stage}</div>
                  <div className="text-xs text-muted-foreground">{j.touchpoint}</div>
                  {j.friction && <div className="mt-1 text-xs text-warning">Friction: {j.friction}</div>}
                </li>
              ))}
            </ol>
          </GlassCard>
        </div>
      )}

      {/* Sales funnel */}
      {!!p.sales_funnel?.length && (
        <div>
          <SectionHeader title="Sales Funnel" icon={ArrowDown} />
          <div className="space-y-2">
            {p.sales_funnel.map((f, i) => (
              <GlassCard key={i} className="flex items-start gap-3 p-4">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 text-xs font-semibold text-violet-500">
                  {i + 1}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium">{f.step}</div>
                  <div className="text-xs text-muted-foreground">{f.purpose}</div>
                  {f.leak_risk && <div className="mt-1 text-xs text-danger">Leak risk: {f.leak_risk}</div>}
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* Pains / desires */}
      {(!!p.pain_points?.length || !!p.desires?.length) && (
        <div className="grid gap-4 lg:grid-cols-2">
          {!!p.pain_points?.length && (
            <GlassCard className="p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Pain Points</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {p.pain_points.map((x, i) => <Chip key={i} tone="danger">{x}</Chip>)}
              </div>
            </GlassCard>
          )}
          {!!p.desires?.length && (
            <GlassCard className="p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Desires</div>
              <div className="mt-3 space-y-2">
                {p.desires.map((d, i) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-lg border border-border/60 p-2.5">
                    <div>
                      <div className="text-sm">{d.desire}</div>
                      {d.evidence && <div className="mt-0.5 text-xs italic text-muted-foreground">"{d.evidence}"</div>}
                    </div>
                    {d.intensity != null && <Chip tone="violet">{String(d.intensity)}</Chip>}
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>
      )}

      {/* Ideal customers */}
      {!!p.ideal_customers?.length && (
        <div>
          <SectionHeader title="Ideal Customers" icon={Users2} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {p.ideal_customers.map((c, i) => (
              <GlassCard key={i} glow className="p-4">
                <div className="text-sm font-semibold">{c.label}</div>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{c.description}</p>
              </GlassCard>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
