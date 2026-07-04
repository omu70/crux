"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Loading } from "@/components/dashboard/common";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@/components/ui";

const INTEGRATIONS = ["META_ADS", "SHOPIFY", "WOOCOMMERCE", "GA4", "SEARCH_CONSOLE", "CLARITY"];

function useSaved() {
  const [saved, setSaved] = useState("");
  const flash = (k: string) => { setSaved(k); setTimeout(() => setSaved(""), 1600); };
  return { saved, flash };
}

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { saved, flash } = useSaved();

  const client = useQuery({ queryKey: ["admin-client", id], queryFn: () => apiGet(`/admin/clients/${id}`) });
  const integrations = useQuery({ queryKey: ["admin-integrations", id], queryFn: () => apiGet(`/admin/clients/${id}/integrations`) });

  const [creds, setCreds] = useState({ username: "", password: "" });
  const [targets, setTargets] = useState({ plan: "", monthly_budget: 0, monthly_target_revenue: 0, monthly_target_roas: 0, monthly_target_leads: 0 });
  const [metric, setMetric] = useState({ date: new Date().toISOString().slice(0, 10), revenue: 0, orders: 0, ad_spend: 0, roas: 0, leads: 0 });
  const [notif, setNotif] = useState({ title: "", message: "" });
  const [task, setTask] = useState({ title: "", priority: "MEDIUM", responsible: "", timeframe: "week" });

  useEffect(() => {
    if (client.data) {
      const c = client.data;
      setTargets({ plan: c.plan, monthly_budget: c.monthly_budget, monthly_target_revenue: c.monthly_target_revenue, monthly_target_roas: c.monthly_target_roas, monthly_target_leads: c.monthly_target_leads });
      setCreds((v) => ({ ...v, username: c.user?.username ?? "" }));
    }
  }, [client.data]);

  const saveCreds = useMutation({ mutationFn: () => apiPatch(`/admin/clients/${id}/credentials`, { username: creds.username, password: creds.password || undefined }), onSuccess: () => { flash("creds"); setCreds((v) => ({ ...v, password: "" })); } });
  const saveTargets = useMutation({ mutationFn: () => apiPatch(`/admin/clients/${id}/targets`, targets), onSuccess: () => { flash("targets"); qc.invalidateQueries({ queryKey: ["admin-client", id] }); } });
  const connect = useMutation({ mutationFn: (type: string) => apiPost(`/admin/clients/${id}/integrations`, { type, status: "CONNECTED", account_name: `${type} account` }), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-integrations", id] }) });
  const addMetric = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/metrics`, { date: metric.date, revenue: metric.revenue, orders: metric.orders, ad_spend: metric.ad_spend, roas: metric.roas || (metric.ad_spend ? +(metric.revenue / metric.ad_spend).toFixed(2) : 0), lead_count: metric.leads, aov: metric.orders ? +(metric.revenue / metric.orders).toFixed(2) : 0 }), onSuccess: () => flash("metric") });
  const sendNotif = useMutation({ mutationFn: () => apiPost(`/admin/notifications`, { client_id: id, title: notif.title, message: notif.message, type: "GENERAL" }), onSuccess: () => { flash("notif"); setNotif({ title: "", message: "" }); } });
  const addTask = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/tasks`, task), onSuccess: () => { flash("task"); setTask({ title: "", priority: "MEDIUM", responsible: "", timeframe: "week" }); } });

  if (client.isLoading) return <Loading />;
  const c = client.data;
  const connected = new Set((integrations.data ?? []).map((i: any) => i.type));

  const Saved = ({ k }: { k: string }) => saved === k ? <span className="inline-flex items-center gap-1 text-xs text-success"><Check className="h-3 w-3" /> Saved</span> : null;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/admin/clients" className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> All clients</Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{c.company_name}</h1>
          <Badge tone={c.status === "ACTIVE" ? "success" : "warning"}>{c.status}</Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{c.contact_name} · {c.user?.email}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Credentials */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Credentials</CardTitle><Saved k="creds" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Username</Label><Input value={creds.username} onChange={(e) => setCreds({ ...creds, username: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Reset password</Label><Input type="text" placeholder="Leave blank to keep" value={creds.password} onChange={(e) => setCreds({ ...creds, password: e.target.value })} /></div>
            <Button size="sm" onClick={() => saveCreds.mutate()}>Save credentials</Button>
          </CardContent>
        </Card>

        {/* Targets */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Plan & Targets</CardTitle><Saved k="targets" /></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Plan</Label><Input value={targets.plan} onChange={(e) => setTargets({ ...targets, plan: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Budget</Label><Input type="number" value={targets.monthly_budget} onChange={(e) => setTargets({ ...targets, monthly_budget: +e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Target revenue</Label><Input type="number" value={targets.monthly_target_revenue} onChange={(e) => setTargets({ ...targets, monthly_target_revenue: +e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Target ROAS</Label><Input type="number" value={targets.monthly_target_roas} onChange={(e) => setTargets({ ...targets, monthly_target_roas: +e.target.value })} /></div>
            <div className="col-span-2"><Button size="sm" onClick={() => saveTargets.mutate()}>Save targets</Button></div>
          </CardContent>
        </Card>

        {/* Integrations */}
        <Card>
          <CardHeader><CardTitle>Integrations</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {INTEGRATIONS.map((t) => (
              <button key={t} onClick={() => connect.mutate(t)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${connected.has(t) ? "border-success/30 bg-success/10 text-success" : "border-border text-muted-foreground hover:bg-muted"}`}>
                {connected.has(t) && <Check className="mr-1 inline h-3 w-3" />}{t.replace(/_/g, " ")}
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Manual metric entry */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Add daily metrics</CardTitle><Saved k="metric" /></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Date</Label><Input type="date" value={metric.date} onChange={(e) => setMetric({ ...metric, date: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Revenue</Label><Input type="number" value={metric.revenue} onChange={(e) => setMetric({ ...metric, revenue: +e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Orders</Label><Input type="number" value={metric.orders} onChange={(e) => setMetric({ ...metric, orders: +e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Ad spend</Label><Input type="number" value={metric.ad_spend} onChange={(e) => setMetric({ ...metric, ad_spend: +e.target.value })} /></div>
            <div className="col-span-2"><Button size="sm" onClick={() => addMetric.mutate()}>Save metrics</Button></div>
          </CardContent>
        </Card>

        {/* Notification */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Send notification</CardTitle><Saved k="notif" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Title</Label><Input value={notif.title} onChange={(e) => setNotif({ ...notif, title: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Message</Label><Input value={notif.message} onChange={(e) => setNotif({ ...notif, message: e.target.value })} /></div>
            <Button size="sm" onClick={() => sendNotif.mutate()} disabled={!notif.title}>Send</Button>
          </CardContent>
        </Card>

        {/* Task */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Create task</CardTitle><Saved k="task" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Title</Label><Input value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Priority</Label>
                <select value={task.priority} onChange={(e) => setTask({ ...task, priority: e.target.value })} className="h-11 w-full rounded-lg border border-input bg-background/60 px-3 text-sm">
                  <option>HIGH</option><option>MEDIUM</option><option>LOW</option>
                </select>
              </div>
              <div className="space-y-1.5"><Label>Responsible</Label><Input value={task.responsible} onChange={(e) => setTask({ ...task, responsible: e.target.value })} /></div>
            </div>
            <Button size="sm" onClick={() => addTask.mutate()} disabled={!task.title}>Add task</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
