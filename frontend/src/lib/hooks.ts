"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { Campaign, DashboardSummary, Insight } from "@/types";

// ── Client dashboard ─────────────────────────────────────────────────────────
export const useSummary = (range = "30d") =>
  useQuery<DashboardSummary>({ queryKey: ["summary", range], queryFn: () => apiGet(`/dashboard/summary?range=${range}`) });

export const useKpis = (range = "30d") =>
  useQuery({ queryKey: ["kpis", range], queryFn: () => apiGet(`/dashboard/kpis?range=${range}`) });

export const useTimeseries = (metrics: string, range = "30d") =>
  useQuery({ queryKey: ["ts", metrics, range], queryFn: () => apiGet(`/dashboard/timeseries?metrics=${metrics}&range=${range}`) });

export const useCampaigns = () =>
  useQuery<{ campaigns: Campaign[]; summary: any }>({ queryKey: ["campaigns"], queryFn: () => apiGet("/marketing/campaigns") });

export const useEcommerce = () => useQuery({ queryKey: ["ecommerce"], queryFn: () => apiGet("/marketing/ecommerce") });
export const useAnalytics = () => useQuery({ queryKey: ["analytics"], queryFn: () => apiGet("/marketing/analytics") });
export const useSearchConsole = () => useQuery({ queryKey: ["gsc"], queryFn: () => apiGet("/marketing/search-console") });
export const useSeo = () => useQuery({ queryKey: ["seo"], queryFn: () => apiGet("/marketing/seo") });

export const useInsights = () => useQuery<Insight[]>({ queryKey: ["insights"], queryFn: () => apiGet("/insights") });
export const usePlan = () => useQuery({ queryKey: ["plan"], queryFn: () => apiGet("/insights/plan") });
export const useReports = () => useQuery({ queryKey: ["reports"], queryFn: () => apiGet("/reports") });

export const useTasks = () => useQuery({ queryKey: ["tasks"], queryFn: () => apiGet("/tasks") });
export const useGoals = () => useQuery({ queryKey: ["goals"], queryFn: () => apiGet("/goals") });
export const useNotifications = () => useQuery({ queryKey: ["notifications"], queryFn: () => apiGet("/notifications") });
export const useDocuments = () => useQuery({ queryKey: ["documents"], queryFn: () => apiGet("/documents") });
export const useTickets = () => useQuery({ queryKey: ["tickets"], queryFn: () => apiGet("/tickets") });
export const useChat = () => useQuery({ queryKey: ["chat"], queryFn: () => apiGet("/chat"), refetchInterval: 8000 });
export const useMeetingNotes = () => useQuery({ queryKey: ["meetings"], queryFn: () => apiGet("/meeting-notes") });
export const usePerformanceScore = () => useQuery({ queryKey: ["score"], queryFn: () => apiGet("/dashboard/performance-score") });
export const useWebsiteHealth = () => useQuery({ queryKey: ["health"], queryFn: () => apiGet("/dashboard/website-health") });
export const useAlerts = () => useQuery({ queryKey: ["alerts"], queryFn: () => apiGet("/dashboard/alerts") });

// ── Admin ────────────────────────────────────────────────────────────────────
export const useAdminOverview = () => useQuery({ queryKey: ["admin-overview"], queryFn: () => apiGet("/admin/overview") });
export const useClients = () => useQuery({ queryKey: ["admin-clients"], queryFn: () => apiGet("/admin/clients") });
export const useApiStatus = () => useQuery({ queryKey: ["api-status"], queryFn: () => apiGet("/admin/api-status") });
export const useAuditLogs = () => useQuery({ queryKey: ["audit"], queryFn: () => apiGet("/admin/audit-logs") });
export const useAccountManagers = () => useQuery({ queryKey: ["managers"], queryFn: () => apiGet("/admin/account-managers") });
