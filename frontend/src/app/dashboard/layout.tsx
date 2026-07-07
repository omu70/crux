"use client";

import {
  Bot, CheckSquare, FileText, FolderOpen, Search, Settings as SettingsIcon,
  LayoutDashboard, LifeBuoy, LineChart, MessageSquare, Megaphone,
  ShoppingCart, Target,
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
  // ── Aether AI — hidden from the client portal for now (admin/internal only) ──
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <Shell nav={nav} role="CLIENT">{children}</Shell>;
}
