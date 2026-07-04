"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { Card } from "@/components/ui";
import { cn, formatKpi } from "@/lib/utils";
import type { KpiCard as KpiCardType } from "@/types";

export function KpiCard({ card, currency }: { card: KpiCardType; currency?: string }) {
  const up = card.delta > 0;
  const down = card.delta < 0;
  return (
    <Card className="p-4 transition-colors hover:border-primary/30">
      <div className="text-xs font-medium text-muted-foreground">{card.label}</div>
      <div className="mt-1.5 text-2xl font-semibold tracking-tight tabular">
        {formatKpi(card.value, card.format, currency)}
      </div>
      <div
        className={cn(
          "mt-1.5 inline-flex items-center gap-1 text-xs font-medium",
          up && "text-success",
          down && "text-danger",
          !up && !down && "text-muted-foreground",
        )}
      >
        {up ? <ArrowUpRight className="h-3.5 w-3.5" /> : down ? <ArrowDownRight className="h-3.5 w-3.5" /> : <Minus className="h-3 w-3" />}
        {Math.abs(card.delta).toFixed(1)}%
        <span className="text-muted-foreground/70">vs prev</span>
      </div>
    </Card>
  );
}

export function KpiGrid({ cards, currency }: { cards: KpiCardType[]; currency?: string }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
      {cards.map((c) => (
        <KpiCard key={c.key} card={c} currency={currency} />
      ))}
    </div>
  );
}
