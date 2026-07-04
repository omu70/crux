"use client";

import { Lightbulb, TrendingUp, TriangleAlert, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui";
import { cn } from "@/lib/utils";
import type { Insight } from "@/types";

const meta: Record<string, { icon: any; tone: "success" | "warning" | "primary" | "default"; ring: string }> = {
  performance: { icon: TrendingUp, tone: "success", ring: "bg-success/10 text-success" },
  warning: { icon: TriangleAlert, tone: "danger" as any, ring: "bg-danger/10 text-danger" },
  opportunity: { icon: Sparkles, tone: "primary", ring: "bg-primary/10 text-primary" },
  recommendation: { icon: Lightbulb, tone: "warning", ring: "bg-warning/10 text-warning" },
};

const impactTone: Record<string, "danger" | "warning" | "default"> = {
  HIGH: "danger", MEDIUM: "warning", LOW: "default",
};

export function InsightCard({ insight }: { insight: Insight }) {
  const m = meta[insight.category] || meta.recommendation;
  const Icon = m.icon;
  return (
    <div className="flex gap-3 rounded-xl border border-border bg-card/60 p-4">
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", m.ring)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-sm font-semibold">{insight.title}</h4>
          <Badge tone={impactTone[insight.impact]} className="shrink-0">{insight.impact}</Badge>
        </div>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{insight.body}</p>
      </div>
    </div>
  );
}
