"use client";

import {
  Bot, Brain, CheckSquare, Eye, FileText, FolderOpen, Search, Settings as SettingsIcon,
  LayoutDashboard, LifeBuoy, LineChart, MessageSquare, Megaphone, PenTool, Rocket,
  ShoppingCart, SlidersHorizontal, Sparkles, Swords, Target, Users,
} from "lucide-react";
import { Shell, type NavItem } from "@/components/dashboard/shell";

const nav: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/ads", label: "Meta Ads", icon: Megaphone },
  { href: "/dashboard/ecommerce", label: "E-commerce", icon: ShoppingCart },
  { href: "/dashboard/analytics", label: "Analytics", icon: LineChart },
  { href: "/dashboard/seo", label: "Search & SEO", icon: Search },
  { href: "/dashboard/insights", label: "AI Insights", icon: Bot },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
  { href: "/dashboard/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/dashboard/goals", label: "Goals", icon: Target },
  { href: "/dashboard/documents", label: "Documents", icon: FolderOpen },
  { href: "/dashboard/support", label: "Support", icon: LifeBuoy },
  { href: "/dashboard/chat", label: "Messages", icon: MessageSquare },
  { href: "/dashboard/settings", label: "Settings", icon: SettingsIcon },
  // ── Aether AI — the AI media buyer that never sleeps ──────────────────────
  { href: "/dashboard/aether", label: "Command Center", icon: Sparkles, section: "Aether AI" },
  { href: "/dashboard/aether/business", label: "Business Intel", icon: Brain, section: "Aether AI" },
  { href: "/dashboard/aether/competitors", label: "Competitors", icon: Swords, section: "Aether AI" },
  { href: "/dashboard/aether/audience", label: "Audience", icon: Users, section: "Aether AI" },
  { href: "/dashboard/aether/studio", label: "Creative Studio", icon: PenTool, section: "Aether AI" },
  { href: "/dashboard/aether/visual", label: "Visual AI", icon: Eye, section: "Aether AI" },
  { href: "/dashboard/aether/launch", label: "Launch", icon: Rocket, section: "Aether AI" },
  { href: "/dashboard/aether/performance", label: "Performance", icon: LineChart, section: "Aether AI" },
  { href: "/dashboard/aether/optimizer", label: "Optimizer", icon: SlidersHorizontal, section: "Aether AI" },
  { href: "/dashboard/aether/research", label: "Research", icon: Search, section: "Aether AI" },
  { href: "/dashboard/aether/council", label: "AI Council", icon: Bot, section: "Aether AI" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <Shell nav={nav} role="CLIENT">{children}</Shell>;
}
