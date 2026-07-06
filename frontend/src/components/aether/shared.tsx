"use client";

// Shared building blocks for the Aether AI module suite.
// Glassmorphism accents (violet/indigo) layered on top of the existing UI kit.

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Check, Copy, Sparkles } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { Badge } from "@/components/ui";
import type { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

/* ── FadeIn — standard entrance ─────────────────────────────────────────── */
export function FadeIn({
  children, delay = 0, className,
}: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ── GlassCard — translucent card with optional gradient top edge ───────── */
export function GlassCard({
  className, glow, ...props
}: React.HTMLAttributes<HTMLDivElement> & { glow?: boolean }) {
  return (
    <div
      className={cn(
        "relative rounded-2xl border border-border/70 bg-white/60 shadow-soft backdrop-blur-xl dark:bg-white/5",
        glow &&
          "before:pointer-events-none before:absolute before:inset-x-6 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-violet-500/70 before:to-transparent",
        className,
      )}
      {...props}
    />
  );
}

/* ── SectionHeader ──────────────────────────────────────────────────────── */
export function SectionHeader({
  title, desc, action, icon: Icon,
}: { title: string; desc?: string; action?: React.ReactNode; icon?: LucideIcon }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="flex items-center gap-2 text-base font-semibold tracking-tight">
          {Icon && (
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/15 to-indigo-500/15 text-violet-500 dark:text-violet-400">
              <Icon className="h-4 w-4" />
            </span>
          )}
          {title}
        </h2>
        {desc && <p className="mt-1 text-xs text-muted-foreground">{desc}</p>}
      </div>
      {action}
    </div>
  );
}

/* ── AetherEmpty — empty state with a CTA ───────────────────────────────── */
export function AetherEmpty({
  icon: Icon = Sparkles, title, desc, cta,
}: { icon?: LucideIcon; title: string; desc?: string; cta?: React.ReactNode }) {
  return (
    <GlassCard glow className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-500/20 text-violet-500 dark:text-violet-400">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-sm font-semibold">{title}</div>
      {desc && <div className="mt-1.5 max-w-md text-xs leading-relaxed text-muted-foreground">{desc}</div>}
      {cta && <div className="mt-5">{cta}</div>}
    </GlassCard>
  );
}

/* ── LoadingAgents — animated "agents thinking" indicator ───────────────── */
export function LoadingAgents({
  label = "Aether agents are working", sub = "Real AI is thinking — this can take up to a minute.",
}: { label?: string; sub?: string }) {
  return (
    <GlassCard glow className="flex flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <div className="relative flex h-12 w-12 items-center justify-center">
        <motion.span
          className="absolute inset-0 rounded-full bg-gradient-to-br from-violet-500/30 to-indigo-500/30"
          animate={{ scale: [1, 1.35, 1], opacity: [0.6, 0.15, 0.6] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
        />
        <Sparkles className="relative h-5 w-5 text-violet-500 dark:text-violet-400" />
      </div>
      <div className="flex items-center gap-1.5 text-sm font-medium">
        {label}
        <span className="flex gap-0.5 pl-0.5">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1 w-1 rounded-full bg-violet-500"
              animate={{ opacity: [0.2, 1, 0.2] }}
              transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.22 }}
            />
          ))}
        </span>
      </div>
      <div className="text-xs text-muted-foreground">{sub}</div>
    </GlassCard>
  );
}

/* ── SeverityBadge ──────────────────────────────────────────────────────── */
const severityTone: Record<string, "primary" | "warning" | "danger" | "default"> = {
  INFO: "primary", WARNING: "warning", CRITICAL: "danger",
};
export function SeverityBadge({ severity }: { severity?: string }) {
  return <Badge tone={severityTone[severity ?? ""] ?? "default"}>{severity ?? "—"}</Badge>;
}

/* ── AgentAvatar — colored initials per agent name ──────────────────────── */
function hashHue(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
  return h;
}
export function AgentAvatar({ name, size = 28 }: { name: string; size?: number }) {
  const hue = hashHue(name || "?");
  const initials = (name || "?")
    .split(/[\s_-]+/)
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-lg font-semibold"
      style={{
        width: size, height: size, fontSize: size * 0.36,
        background: `hsl(${hue} 70% 50% / 0.16)`,
        color: `hsl(${hue} 72% 52%)`,
      }}
      title={name}
    >
      {initials}
    </div>
  );
}

/* ── Score visuals ──────────────────────────────────────────────────────── */
export function scoreColor(v: number) {
  return v >= 80 ? "hsl(var(--success))" : v >= 60 ? "hsl(var(--warning))" : v >= 40 ? "hsl(25 90% 55%)" : "hsl(var(--danger))";
}

export function ScoreBar({
  value = 0, label, className,
}: { value?: number; label?: string; className?: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("space-y-1", className)}>
      {label && (
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>{label}</span>
          <span className="font-medium tabular text-foreground">{Math.round(v)}</span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${v}%`, background: scoreColor(v) }}
        />
      </div>
    </div>
  );
}

/* ── Chip — small pill for tags / verbatim language ─────────────────────── */
export function Chip({
  children, tone = "default", className,
}: { children: React.ReactNode; tone?: "default" | "violet" | "success" | "danger"; className?: string }) {
  const tones = {
    default: "bg-muted text-muted-foreground",
    violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20",
    success: "bg-success/10 text-success border border-success/20",
    danger: "bg-danger/10 text-danger border border-danger/20",
  };
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs", tones[tone], className)}>
      {children}
    </span>
  );
}

/* ── ErrorNote — surfaces ApiError; 402 → upgrade hint ──────────────────── */
export function ErrorNote({ error }: { error?: unknown }) {
  if (!error) return null;
  const e = error as Partial<ApiError>;
  const status = typeof e?.status === "number" ? e.status : undefined;
  const msg = (e as Error)?.message || "Something went wrong.";
  return (
    <div className="rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-xs text-danger">
      <span className="font-medium">{status ? `Error ${status}: ` : ""}</span>
      {msg}
      {status === 402 && (
        <>
          {" — you've hit your plan limit. "}
          <Link href="/dashboard/aether#billing" className="font-medium underline underline-offset-2">
            Upgrade your Aether plan
          </Link>
        </>
      )}
    </div>
  );
}

/* ── Form primitives missing from the base kit ──────────────────────────── */
export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "flex h-11 w-full appearance-none rounded-lg border border-input bg-background/60 px-3.5 text-sm",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-transparent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = "Select";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[88px] w-full rounded-lg border border-input bg-background/60 px-3.5 py-2.5 text-sm",
        "placeholder:text-muted-foreground/70 transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-transparent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

/* ── CopyButton ─────────────────────────────────────────────────────────── */
export function CopyButton({ text, className }: { text: string; className?: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className={cn(
        "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
        className,
      )}
      aria-label="Copy to clipboard"
      title="Copy to clipboard"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

/* ── Tabs — simple pill tab bar ─────────────────────────────────────────── */
export function PillTabs({
  tabs, value, onChange, className,
}: { tabs: { key: string; label: string }[]; value: string; onChange: (v: string) => void; className?: string }) {
  return (
    <div className={cn("inline-flex flex-wrap gap-1 rounded-lg border border-border bg-card/60 p-1", className)}>
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
            value === t.key
              ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-soft"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ── PrettyJson ─────────────────────────────────────────────────────────── */
export function PrettyJson({ data, className }: { data: any; className?: string }) {
  return (
    <pre className={cn("max-h-56 overflow-auto rounded-lg border border-border bg-muted/50 p-3 text-[11px] leading-relaxed text-muted-foreground", className)}>
      {typeof data === "string" ? data : JSON.stringify(data ?? {}, null, 2)}
    </pre>
  );
}

/* ── KV — render an unknown object as key/value rows ────────────────────── */
export function KV({ data }: { data: any }) {
  if (data == null) return <span className="text-xs text-muted-foreground">—</span>;
  if (typeof data !== "object") return <span className="text-sm">{String(data)}</span>;
  const entries = Object.entries(data as Record<string, any>);
  if (!entries.length) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <div className="space-y-1.5">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-start gap-2 text-xs">
          <span className="min-w-[110px] shrink-0 font-medium capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span>
          <span className="text-foreground/90">
            {typeof v === "object" ? JSON.stringify(v) : String(v)}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── Helpers ────────────────────────────────────────────────────────────── */
export function contentToText(content: any): string {
  if (content == null) return "";
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.map(contentToText).join("\n");
  return Object.entries(content as Record<string, any>)
    .map(([k, v]) => `${k.replace(/_/g, " ").toUpperCase()}: ${typeof v === "object" ? JSON.stringify(v) : v}`)
    .join("\n");
}

export function timeAgo(iso?: string | null) {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}
