"use client";

// Aether AI — typed API client + React Query hooks for every /api/aether endpoint.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPatch, apiPost } from "@/lib/api";

/* ═══════════════════════════ Types ═══════════════════════════ */

export interface Offer { name?: string; price?: string | number; type?: string; angle?: string }

export interface BusinessProfile {
  id: string;
  status?: string;
  website_url?: string | null;
  summary?: string;
  usp?: string;
  positioning?: string;
  brand_voice?: string;
  visual_style?: string;
  offers?: Offer[];
  price_analysis?: { tier?: string; vs_market?: string; opportunities?: string[] };
  strengths?: string[];
  weaknesses?: string[];
  customer_journey?: { stage?: string; touchpoint?: string; friction?: string }[];
  sales_funnel?: { step?: string; purpose?: string; leak_risk?: string }[];
  pain_points?: string[];
  desires?: { desire?: string; intensity?: string | number; evidence?: string }[];
  ideal_customers?: { label?: string; description?: string }[];
  created_at?: string;
  updated_at?: string;
}

export interface KnowledgeDoc {
  id: string; title: string; namespace?: string; source_type?: string;
  source_url?: string | null; created_at?: string; chunks?: number;
}
export interface KnowledgeHit { content: string; score: number; title?: string; namespace?: string; document_id?: string }

export interface Competitor {
  id: string;
  name: string;
  website?: string | null;
  threat_level?: string;
  pricing?: any;
  offers?: any[];
  creative_angles?: string[];
  headlines?: string[];
  funnels?: any[];
  reviews_summary?: { positives?: string[]; negatives?: string[]; themes?: string[] };
  ads?: any;
  seo?: any;
  content_strategy?: string[];
  email_funnels?: any[];
  swot?: { strengths?: string[]; weaknesses?: string[]; opportunities?: string[]; threats?: string[] };
  positioning_gap?: string;
  last_analyzed_at?: string | null;
}

export interface Persona {
  id: string;
  name: string;
  segment?: string;
  awareness_level?: string;
  sophistication?: number | string;
  purchase_intent?: string | number;
  pains?: string[];
  fears?: string[];
  dream_outcome?: string[];
  objections?: { objection?: string; rebuttal?: string }[];
  buying_triggers?: string[];
  identity?: { self_image?: string; aspiration?: string; tribe?: string };
  lifestyle?: string[];
  language?: string[];
  behavior?: { channels?: string[]; content?: string[]; buying_habits?: string };
  jobs_to_be_done?: { job?: string; context?: string; outcome?: string }[];
  emotional_triggers?: string[];
  targeting?: { interests?: string[]; behaviors?: string[]; age_range?: string; notes?: string };
}
export interface AudienceGenResult {
  market?: { market_sophistication?: string | number; market_notes?: string };
  personas: Persona[];
}

export interface CreativeOptions { kinds: string[]; frameworks: string[] }
export type CreativeStatus = "DRAFT" | "APPROVED" | "IN_USE" | "RETIRED" | "WINNER";
export interface CreativeAsset {
  id: string;
  kind: string;
  framework?: string;
  content: any;
  meta?: { angle?: string; awareness_level?: string; why_it_works?: string; visual_direction?: string };
  predicted_score?: number;
  status: CreativeStatus;
  persona_id?: string | null;
  batch_id?: string | null;
  created_at?: string;
}

export interface VisualAnalysis {
  id: string;
  asset_url: string;
  kind?: string;
  creative_score?: number;
  attention_score?: number;
  scroll_stop_score?: number;
  brand_score?: number;
  emotion_score?: number;
  ctr_prediction?: number;
  recommendations?: string[];
  observations?: string[];
  provider?: string;
  created_at?: string;
}

export interface BlueprintAd { name?: string; headline?: string; primary_text?: string; cta_type?: string; link?: string }
export interface BlueprintAdSet {
  name?: string; audience?: string; targeting?: any; optimization_goal?: string;
  conversion_event?: string; placements?: string[]; budget_share_pct?: number; ads?: BlueprintAd[];
}
export interface Blueprint {
  id: string;
  name?: string;
  objective?: string;
  status?: string;
  daily_budget?: number;
  structure?: { campaign?: any; ad_sets?: BlueprintAdSet[] };
  naming?: any;
  budget_plan?: any;
  audience_strategy?: any;
  pixel_mapping?: any;
  creative_rotation?: any;
  scaling_plan?: { vertical?: string; horizontal?: string; triggers?: string[] };
  published_ids?: any;
  rationale?: string;
  created_at?: string;
}
export interface PublishResult {
  blueprint: Blueprint;
  publish_result: { mode?: string; campaign_id?: string; ad_sets?: any; note?: string };
}

export interface PerfCampaign {
  name: string; status?: string; spend?: number; roas?: number; ctr?: number; cpa?: number;
  cpm?: number; frequency?: number; conversions?: number; impressions?: number; clicks?: number; revenue?: number;
}
export interface PerfAverages { roas?: number; ctr?: number; cpa?: number; cpm?: number; conversion_rate?: number; aov?: number }
export interface PerformanceAnalysis {
  snapshot?: {
    days?: number;
    totals?: { spend?: number; revenue?: number; orders?: number; leads?: number };
    recent_avg?: PerfAverages;
    prev_avg?: PerfAverages;
    campaigns?: PerfCampaign[];
  };
  brief?: {
    headline?: string;
    binding_constraint?: string;
    winners?: { campaign?: string; why_winning?: string; action?: string }[];
    losers?: { campaign?: string; why_failing?: string; action?: string }[];
    funnel_diagnosis?: { stage?: string; health?: string; evidence?: string; fix?: string }[];
    risks?: string[];
    seven_day_plan?: { day?: string | number; action?: string }[];
  };
}

export interface CampaignScore {
  id: string;
  campaign_id?: string;
  date?: string;
  overall?: number;
  dimensions?: {
    creative?: number; audience?: number; offer?: number; landing_page?: number;
    tracking?: number; brand?: number; scaling?: number;
  };
  details?: any;
}

export type Severity = "INFO" | "WARNING" | "CRITICAL";
export interface FatigueSignal {
  id: string;
  entity_type?: string;
  entity_ref?: string;
  fatigue_type?: string;
  severity: Severity;
  evidence?: any;
  recommendation?: string;
  resolved?: boolean;
  created_at?: string;
}
export interface RefreshResult { generated?: number; kind?: string; asset_ids?: string[] }

export type ActionStatus = "PROPOSED" | "APPLIED" | "DISMISSED";
export interface BudgetAction {
  id: string;
  campaign_ref?: string;
  action?: string;
  amount?: { magnitude_pct?: number; trigger?: string; rollback?: string };
  reason?: string;
  confidence?: number;
  expected_impact?: string;
  status: ActionStatus;
  created_at?: string;
}

export interface ResearchJob {
  id: string;
  query: string;
  sources?: string[];
  status?: string;
  results?: any;
  summary?: string;
  insights?: { insight?: string; evidence?: string; marketing_use?: string }[];
  voice_of_customer?: { phrase?: string; emotion?: string; use_as?: string }[];
  created_at?: string;
  finished_at?: string | null;
}

export interface CouncilVote { voter?: string; vote_for?: string; confidence?: number; reason?: string }
export interface CouncilMessage { agent?: string; action?: string; content?: string }
export interface CouncilRun {
  id: string;
  kind?: string;
  status?: string;
  input?: any;
  steps?: any;
  messages?: CouncilMessage[];
  votes?: CouncilVote[];
  decision?: {
    plan?: any;
    decision?: { decision?: string; why?: string; risks?: string[]; kill_criteria?: string[]; first_48h_actions?: string[] };
    review?: { verdict?: string; defects?: string[]; notes?: string };
  };
  tokens_in?: number;
  tokens_out?: number;
  cost_usd?: number;
  created_at?: string;
}

export interface UsageSummary {
  days?: number;
  by_provider?: { provider?: string; kind?: string; tokens_in?: number; tokens_out?: number; cost_usd?: number }[];
  total_cost_usd?: number;
}

export interface AutomationRun { id: string; kind?: string; status?: string; output?: any; created_at?: string }

export interface BillingPlan { name: string; price_usd: number; limits?: Record<string, any> }
export type BillingPlans = Record<string, BillingPlan>;
export interface Subscription {
  plan?: string; plan_name?: string; price_usd?: number; status?: string;
  limits?: Record<string, any>; current_period_end?: string | null;
}

/* ═══════════════════════════ Query keys ═══════════════════════════ */

const K = {
  profile: ["aether", "business", "profile"] as const,
  docs: ["aether", "knowledge", "docs"] as const,
  competitors: ["aether", "competitors"] as const,
  personas: ["aether", "personas"] as const,
  creativeOptions: ["aether", "creatives", "options"] as const,
  creatives: (f: string) => ["aether", "creatives", f] as const,
  visual: ["aether", "visual"] as const,
  blueprints: ["aether", "blueprints"] as const,
  performance: (days: number) => ["aether", "performance", days] as const,
  scores: ["aether", "scores"] as const,
  fatigue: ["aether", "fatigue"] as const,
  actions: (s: string) => ["aether", "actions", s] as const,
  researchSources: ["aether", "research", "sources"] as const,
  research: ["aether", "research", "jobs"] as const,
  rosters: ["aether", "agents", "rosters"] as const,
  runs: ["aether", "agents", "runs"] as const,
  run: (id: string) => ["aether", "agents", "run", id] as const,
  usage: ["aether", "usage"] as const,
  automations: ["aether", "automations"] as const,
  plans: ["aether", "billing", "plans"] as const,
  subscription: ["aether", "billing", "subscription"] as const,
};

/* ═══════════════════ Business Intelligence + Knowledge ═══════════════════ */

export const useBusinessProfile = () =>
  useQuery<BusinessProfile | null>({
    queryKey: K.profile,
    retry: false,
    queryFn: () =>
      apiGet<BusinessProfile>("/aether/business/profile").catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      }),
  });

export const useAnalyzeBusiness = () => {
  const qc = useQueryClient();
  return useMutation<BusinessProfile, ApiError, { website_url?: string; extra_text?: string; social_urls: string[] }>({
    mutationFn: (body) => apiPost("/aether/business/analyze", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.profile }),
  });
};

export const useKnowledgeDocs = () =>
  useQuery<KnowledgeDoc[]>({ queryKey: K.docs, queryFn: () => apiGet("/aether/knowledge/documents") });

export const useUploadKnowledge = () => {
  const qc = useQueryClient();
  return useMutation<KnowledgeDoc, ApiError, { file: File; namespace: string }>({
    mutationFn: ({ file, namespace }) => {
      const fd = new FormData();
      fd.append("file", file);
      return apiPost(`/aether/knowledge/upload?namespace=${encodeURIComponent(namespace)}`, fd);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: K.docs }),
  });
};

export const useKnowledgeSearch = () =>
  useMutation<KnowledgeHit[], ApiError, { query: string; namespace?: string; k?: number }>({
    mutationFn: (body) => apiPost("/aether/knowledge/search", body),
  });

/* ═══════════════════ Competitors ═══════════════════ */

export const useCompetitors = () =>
  useQuery<Competitor[]>({ queryKey: K.competitors, queryFn: () => apiGet("/aether/competitors") });

export const useDiscoverCompetitors = () => {
  const qc = useQueryClient();
  return useMutation<Competitor[], ApiError, { count: number; industry_hint: string }>({
    mutationFn: (body) => apiPost("/aether/competitors/discover", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.competitors }),
  });
};

export const useAnalyzeCompetitor = () => {
  const qc = useQueryClient();
  return useMutation<Competitor, ApiError, string>({
    mutationFn: (id) => apiPost(`/aether/competitors/${id}/analyze`),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.competitors }),
  });
};

/* ═══════════════════ Audience ═══════════════════ */

export const usePersonas = () =>
  useQuery<Persona[]>({ queryKey: K.personas, queryFn: () => apiGet("/aether/audience/personas") });

export const useGeneratePersonas = () => {
  const qc = useQueryClient();
  return useMutation<AudienceGenResult, ApiError, { count: number; focus: string }>({
    mutationFn: (body) => apiPost("/aether/audience/generate", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.personas }),
  });
};

/* ═══════════════════ Creatives ═══════════════════ */

export const useCreativeOptions = () =>
  useQuery<CreativeOptions>({ queryKey: K.creativeOptions, queryFn: () => apiGet("/aether/creatives/options"), staleTime: 300_000 });

export const useCreatives = (params: { kind?: string; status?: string; limit?: number } = {}) => {
  const qs = new URLSearchParams();
  if (params.kind) qs.set("kind", params.kind);
  if (params.status) qs.set("status", params.status);
  if (params.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return useQuery<CreativeAsset[]>({
    queryKey: K.creatives(query),
    queryFn: () => apiGet(`/aether/creatives${query ? `?${query}` : ""}`),
  });
};

export const useGenerateCreatives = () => {
  const qc = useQueryClient();
  return useMutation<CreativeAsset[], ApiError, { kind: string; count: number; persona_id?: string; framework?: string; product_hint: string }>({
    mutationFn: (body) => apiPost("/aether/creatives/generate", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aether", "creatives"] }),
  });
};

export const useUpdateCreative = () => {
  const qc = useQueryClient();
  return useMutation<CreativeAsset, ApiError, { id: string; status: CreativeStatus }>({
    mutationFn: ({ id, status }) => apiPatch(`/aether/creatives/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aether", "creatives"] }),
  });
};

/* ═══════════════════ Visual AI ═══════════════════ */

export const useVisualHistory = () =>
  useQuery<VisualAnalysis[]>({ queryKey: K.visual, queryFn: () => apiGet("/aether/visual") });

export const useAnalyzeVisual = () => {
  const qc = useQueryClient();
  return useMutation<VisualAnalysis, ApiError, { asset_url: string; kind: string }>({
    mutationFn: (body) => apiPost("/aether/visual/analyze", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.visual }),
  });
};

/* ═══════════════════ Campaign Builder ═══════════════════ */

export const useBlueprints = () =>
  useQuery<Blueprint[]>({ queryKey: K.blueprints, queryFn: () => apiGet("/aether/campaigns/blueprints") });

export const useBuildBlueprint = () => {
  const qc = useQueryClient();
  return useMutation<Blueprint, ApiError, { goal: string; daily_budget: number; persona_ids: string[]; landing_url: string }>({
    mutationFn: (body) => apiPost("/aether/campaigns/build", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.blueprints }),
  });
};

export const usePublishBlueprint = () => {
  const qc = useQueryClient();
  return useMutation<PublishResult, ApiError, string>({
    mutationFn: (id) => apiPost(`/aether/campaigns/blueprints/${id}/publish`),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.blueprints }),
  });
};

/* ═══════════════════ Performance ═══════════════════ */

export const usePerformanceAnalysis = (days = 14) =>
  useQuery<PerformanceAnalysis>({
    queryKey: K.performance(days),
    queryFn: () => apiGet(`/aether/performance/analysis?days=${days}`),
  });

export const useScores = () =>
  useQuery<CampaignScore[]>({ queryKey: K.scores, queryFn: () => apiGet("/aether/performance/scores") });

export const useGenerateScores = () => {
  const qc = useQueryClient();
  return useMutation<CampaignScore[], ApiError, void>({
    mutationFn: () => apiPost("/aether/performance/scores/generate"),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.scores }),
  });
};

/* ═══════════════════ Optimizer ═══════════════════ */

export const useFatigueSignals = () =>
  useQuery<FatigueSignal[]>({ queryKey: K.fatigue, queryFn: () => apiGet("/aether/optimizer/fatigue") });

export const useScanFatigue = () => {
  const qc = useQueryClient();
  return useMutation<FatigueSignal[], ApiError, void>({
    mutationFn: () => apiPost("/aether/optimizer/fatigue/scan"),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.fatigue }),
  });
};

export const useRefreshFatigue = () => {
  const qc = useQueryClient();
  return useMutation<RefreshResult, ApiError, string>({
    mutationFn: (id) => apiPost(`/aether/optimizer/fatigue/${id}/refresh`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: K.fatigue });
      qc.invalidateQueries({ queryKey: ["aether", "creatives"] });
    },
  });
};

export const useBudgetActions = (status?: string) =>
  useQuery<BudgetAction[]>({
    queryKey: K.actions(status ?? ""),
    queryFn: () => apiGet(`/aether/optimizer/actions${status ? `?status=${status}` : ""}`),
  });

export const useBudgetReview = () => {
  const qc = useQueryClient();
  return useMutation<BudgetAction[], ApiError, void>({
    mutationFn: () => apiPost("/aether/optimizer/budget/review"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aether", "actions"] }),
  });
};

export const useApplyAction = () => {
  const qc = useQueryClient();
  return useMutation<{ action: BudgetAction; result: any }, ApiError, string>({
    mutationFn: (id) => apiPost(`/aether/optimizer/actions/${id}/apply`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aether", "actions"] }),
  });
};

export const useDismissAction = () => {
  const qc = useQueryClient();
  return useMutation<BudgetAction, ApiError, string>({
    mutationFn: (id) => apiPost(`/aether/optimizer/actions/${id}/dismiss`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aether", "actions"] }),
  });
};

/* ═══════════════════ Research ═══════════════════ */

export const useResearchSources = () =>
  useQuery<{ sources: string[] }>({ queryKey: K.researchSources, queryFn: () => apiGet("/aether/research/sources"), staleTime: 300_000 });

export const useResearchJobs = () =>
  useQuery<ResearchJob[]>({ queryKey: K.research, queryFn: () => apiGet("/aether/research") });

export const useRunResearch = () => {
  const qc = useQueryClient();
  return useMutation<ResearchJob, ApiError, { query: string; sources: string[] }>({
    mutationFn: (body) => apiPost("/aether/research", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.research }),
  });
};

/* ═══════════════════ Agent Council ═══════════════════ */

export const useRosters = () =>
  useQuery<Record<string, string[]>>({ queryKey: K.rosters, queryFn: () => apiGet("/aether/agents/rosters"), staleTime: 300_000 });

export const useCouncilRuns = () =>
  useQuery<CouncilRun[]>({ queryKey: K.runs, queryFn: () => apiGet("/aether/agents/runs") });

export const useCouncilRun = (id?: string | null) =>
  useQuery<CouncilRun>({
    queryKey: K.run(id ?? ""),
    queryFn: () => apiGet(`/aether/agents/runs/${id}`),
    enabled: !!id,
  });

export const useRunCouncil = () => {
  const qc = useQueryClient();
  return useMutation<CouncilRun, ApiError, { kind: string; question: string; context: string }>({
    mutationFn: (body) => apiPost("/aether/agents/council", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.runs }),
  });
};

/* ═══════════════════ Usage / Automations / Billing ═══════════════════ */

export const useUsageSummary = () =>
  useQuery<UsageSummary>({ queryKey: K.usage, queryFn: () => apiGet("/aether/usage/summary") });

export const useAutomationRuns = () =>
  useQuery<AutomationRun[]>({ queryKey: K.automations, queryFn: () => apiGet("/aether/automations/runs") });

export const useMorningReport = () => {
  const qc = useQueryClient();
  return useMutation<any, ApiError, void>({
    mutationFn: () => apiPost("/aether/automations/morning-report"),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.automations }),
  });
};

export const useBillingPlans = () =>
  useQuery<BillingPlans>({ queryKey: K.plans, queryFn: () => apiGet("/aether/billing/plans"), staleTime: 300_000 });

export const useSubscription = () =>
  useQuery<Subscription>({ queryKey: K.subscription, queryFn: () => apiGet("/aether/billing/subscription") });

export const useCheckout = () => {
  const qc = useQueryClient();
  return useMutation<{ mode?: string; url?: string }, ApiError, { plan: string }>({
    mutationFn: (body) => apiPost("/aether/billing/checkout", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: K.subscription }),
  });
};
