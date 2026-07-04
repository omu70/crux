import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number, opts: Intl.NumberFormatOptions = {}) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0, ...opts }).format(n ?? 0);
}

export function formatCompact(n: number) {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n ?? 0);
}

export function formatCurrency(n: number, currency = "USD", compact = false) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: compact ? 1 : 0,
    notation: compact ? "compact" : "standard",
  }).format(n ?? 0);
}

/** Format a KPI card value according to its `format` field. */
export function formatKpi(value: number, format: string, currency = "USD") {
  switch (format) {
    case "currency":
      return formatCurrency(value, currency, Math.abs(value) >= 100000);
    case "percent":
      return `${(value ?? 0).toFixed(2)}%`;
    case "ratio":
      return `${(value ?? 0).toFixed(2)}x`;
    default:
      return formatCompact(value);
  }
}

export function classForDelta(delta: number) {
  if (delta > 0) return "text-success";
  if (delta < 0) return "text-danger";
  return "text-muted-foreground";
}
