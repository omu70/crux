"use client";

import { Activity, LayoutDashboard, Users } from "lucide-react";
import { usePathname } from "next/navigation";
import { Shell, type NavItem } from "@/components/dashboard/shell";

const nav: NavItem[] = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard },
  { href: "/admin/clients", label: "Clients", icon: Users },
  { href: "/admin/logs", label: "Activity & API", icon: Activity },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // The admin login page must not be wrapped in the protected shell.
  if (pathname === "/admin/login") return <>{children}</>;
  return <Shell nav={nav} role="ADMIN">{children}</Shell>;
}
