export type KpiCard = {
  key: string;
  label: string;
  value: number;
  format: "number" | "currency" | "percent" | "ratio";
  delta: number;
};

export type AccountManager = { name: string; title: string; email: string; avatar_url?: string | null };

export type DashboardSummary = {
  greeting: string;
  client: {
    company_name: string;
    contact_name: string;
    plan: string;
    monthly_budget: number;
    currency: string;
    current_month: string;
    account_manager: AccountManager | null;
    targets: { revenue: number; roas: number; leads: number };
  };
  range: { start: string; end: string; key: string };
  kpis: KpiCard[];
};

export type Insight = {
  id?: string;
  title: string;
  body: string;
  category: "performance" | "warning" | "opportunity" | "recommendation";
  impact: "LOW" | "MEDIUM" | "HIGH";
};

export type Campaign = {
  id: string;
  name: string;
  status: "ACTIVE" | "PAUSED" | "REJECTED" | "LEARNING";
  spend: number;
  revenue: number;
  purchase_roas: number;
  ctr: number;
  cpa: number;
  cpm: number;
  clicks: number;
  impressions: number;
  reach: number;
  conversions: number;
  is_winning: boolean;
  is_losing: boolean;
};

export type ClientRow = {
  id: string;
  company_name: string;
  contact_name: string;
  plan: string;
  status: "ACTIVE" | "SUSPENDED";
  monthly_budget: number;
  account_manager?: AccountManager | null;
  user?: { username: string; email: string } | null;
  created_at: string;
};
