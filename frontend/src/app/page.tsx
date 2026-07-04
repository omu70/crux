"use client";

import { motion } from "framer-motion";
import {
  ArrowRight, BarChart3, Bot, Facebook, Gauge, LineChart, Search,
  ShoppingCart, Sparkles, TrendingUp, Zap,
} from "lucide-react";
import Link from "next/link";
import { Logo } from "@/components/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button, Card } from "@/components/ui";

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay, ease: "easeOut" as const },
});

const features = [
  { icon: Facebook, title: "Meta Ads", desc: "Campaigns, ad sets, ROAS, CPA, learning phase and winning creatives — synced automatically." },
  { icon: ShoppingCart, title: "Orders & Revenue", desc: "Shopify & WooCommerce orders, AOV, top products, refunds and inventory alerts." },
  { icon: LineChart, title: "Website Analytics", desc: "GA4 sessions, traffic sources, devices and geography in one clean view." },
  { icon: Search, title: "Search & SEO", desc: "Search Console clicks, keywords, positions, backlinks and technical health." },
  { icon: Bot, title: "AI Insights", desc: "Daily, specific recommendations: what's working, what's losing money, what to do next." },
  { icon: BarChart3, title: "Growth Reports", desc: "Executive monthly reports with wins, losses, KPIs and next-month strategy." },
];

export default function LandingPage() {
  return (
    <div className="aurora min-h-screen">
      <div className="relative z-10">
        {/* Nav */}
        <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Logo />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="outline" size="sm">Client Login</Button>
            </Link>
          </div>
        </header>

        {/* Hero */}
        <section className="mx-auto max-w-6xl px-6 pb-8 pt-16 text-center sm:pt-24">
          <motion.div {...fade(0)} className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3.5 py-1.5 text-xs text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Where Growth Becomes Crystal Clear
          </motion.div>

          <motion.h1 {...fade(0.06)} className="mx-auto max-w-3xl text-balance text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            Know exactly where your{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">business is growing.</span>
          </motion.h1>

          <motion.p {...fade(0.12)} className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
            Your complete marketing command center. Track Meta Ads, Orders, Revenue, ROAS,
            Website Performance, Growth Reports and AI Insights from one beautiful dashboard.
          </motion.p>

          <motion.div {...fade(0.18)} className="mt-9 flex items-center justify-center">
            <Link href="/login">
              <Button size="lg" className="group h-12 px-7 text-[15px]">
                Client Login
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Button>
            </Link>
          </motion.div>
          <motion.p {...fade(0.24)} className="mt-4 text-sm text-muted-foreground">
            No signup. No pricing. Only authorized clients.
          </motion.p>

          {/* Floating dashboard preview */}
          <motion.div {...fade(0.3)} className="relative mx-auto mt-16 max-w-5xl">
            <div className="grid-bg absolute inset-x-0 -top-10 h-64" />
            <Card glass className="relative overflow-hidden p-2 shadow-glass">
              <div className="rounded-xl border border-border bg-background/50 p-5">
                <div className="mb-5 flex items-center justify-between">
                  <div className="text-left">
                    <div className="text-sm text-muted-foreground">Good Morning, Lumina Skincare 👋</div>
                    <div className="text-xs text-muted-foreground/70">Scale plan · July 2026</div>
                  </div>
                  <Zap className="h-4 w-4 text-primary" />
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { l: "Revenue", v: "$142.8K", d: "+23%" },
                    { l: "ROAS", v: "4.62x", d: "+8%" },
                    { l: "Orders", v: "1,204", d: "+14%" },
                    { l: "CPA", v: "$22.40", d: "-11%" },
                  ].map((k) => (
                    <div key={k.l} className="rounded-lg border border-border bg-card/70 p-3 text-left">
                      <div className="text-xs text-muted-foreground">{k.l}</div>
                      <div className="mt-1 text-lg font-semibold tabular">{k.v}</div>
                      <div className="mt-0.5 flex items-center gap-1 text-xs text-success">
                        <TrendingUp className="h-3 w-3" /> {k.d}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex h-28 items-end gap-1.5 rounded-lg border border-border bg-card/70 p-3">
                  {[38, 52, 44, 61, 55, 72, 66, 80, 74, 88, 82, 95].map((h, i) => (
                    <div key={i} className="flex-1 rounded-t bg-gradient-to-t from-primary/40 to-primary" style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-semibold tracking-tight">Everything, in one command center</h2>
            <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
              Enterprise-grade clarity across every channel that drives your growth.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div key={f.title} {...fade(i * 0.04)}>
                <Card className="h-full p-6 transition-colors hover:border-primary/40">
                  <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <f.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* CTA band */}
        <section className="mx-auto max-w-6xl px-6 pb-24">
          <Card glass className="relative overflow-hidden p-10 text-center sm:p-16">
            <div className="aurora absolute inset-0 opacity-60" />
            <div className="relative">
              <Gauge className="mx-auto mb-4 h-8 w-8 text-primary" />
              <h2 className="text-3xl font-semibold tracking-tight">Your growth, crystal clear.</h2>
              <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
                Sign in to your private client portal to see live performance, AI insights and your next plan of action.
              </p>
              <Link href="/login" className="mt-8 inline-block">
                <Button size="lg" className="h-12 px-7">Client Login <ArrowRight className="h-4 w-4" /></Button>
              </Link>
            </div>
          </Card>
        </section>

        {/* Footer */}
        <footer className="border-t border-border">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
            <Logo subtitle={false} />
            <p className="text-sm text-muted-foreground">Powered by DiziGroww · © {new Date().getFullYear()}</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
