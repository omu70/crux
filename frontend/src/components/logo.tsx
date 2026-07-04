import { cn } from "@/lib/utils";

export function CruxMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("h-7 w-7", className)} aria-hidden>
      <defs>
        <linearGradient id="cruxg" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="hsl(243 75% 66%)" />
          <stop offset="1" stopColor="hsl(250 90% 72%)" />
        </linearGradient>
      </defs>
      <path d="M16 2 3 9v14l13 7 13-7V9L16 2Z" stroke="url(#cruxg)" strokeWidth="1.6" className="opacity-40" />
      <path d="M16 7 8 11.3v9.4L16 25l8-4.3v-9.4L16 7Z" fill="url(#cruxg)" fillOpacity="0.16" stroke="url(#cruxg)" strokeWidth="1.6" />
      <path d="M16 12v8M12 14l8 4M20 14l-8 4" stroke="url(#cruxg)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, subtitle = true }: { className?: string; subtitle?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <CruxMark />
      <div className="leading-none">
        <div className="text-lg font-semibold tracking-tight">CRUX</div>
        {subtitle && <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">by DiziGroww</div>}
      </div>
    </div>
  );
}
