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
  const [metaAccount, setMetaAccount] = useState("");
  const [syncMsg, setSyncMsg] = useState("");
  const [importMsg, setImportMsg] = useState("");
  const [woo, setWoo] = useState({ url: "", key: "", secret: "" });
  const [wooMsg, setWooMsg] = useState("");

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
  const connectMeta = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/integrations/meta/connect`, { ad_account_id: metaAccount }), onSuccess: () => { flash("meta"); qc.invalidateQueries({ queryKey: ["admin-integrations", id] }); } });
  const syncMeta = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/integrations/meta/sync`), onSuccess: (r: any) => setSyncMsg(`Synced ${r.campaigns_synced} campaigns · ${r.days_synced} days ✓`), onError: (e: any) => setSyncMsg(e.message) });
  const importFile = useMutation({ mutationFn: (file: File) => { const fd = new FormData(); fd.append("file", file); return apiPost(`/admin/clients/${id}/metrics/import`, fd); }, onSuccess: (r: any) => setImportMsg(`Imported ${r.days_imported} days · ${r.campaigns_imported} campaigns ✓`), onError: (e: any) => setImportMsg(e.message) });
  const connectWoo = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/integrations/woocommerce/connect`, woo), onSuccess: () => { flash("woo"); qc.invalidateQueries({ queryKey: ["admin-integrations", id] }); } });
  const syncWoo = useMutation({ mutationFn: () => apiPost(`/admin/clients/${id}/integrations/woocommerce/sync`), onSuccess: (r: any) => setWooMsg(`Synced ${r.orders_synced} orders · ${r.days_updated} days ✓`), onError: (e: any) => setWooMsg(e.message) });

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

        {/* Meta Ads — live sync */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Meta Ads — Live Sync</CardTitle><Saved k="meta" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <Label>Ad Account ID</Label>
              <Input value={metaAccount} onChange={(e) => setMetaAccount(e.target.value)} placeholder="act_1234567890" />
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => connectMeta.mutate()} disabled={!metaAccount || connectMeta.isPending}>Connect</Button>
              <Button size="sm" onClick={() => { setSyncMsg("Syncing…"); syncMeta.mutate(); }} disabled={syncMeta.isPending}>Sync now</Button>
            </div>
            {syncMsg && <p className="text-xs text-muted-foreground">{syncMsg}</p>}
            <p className="text-xs text-muted-foreground">Set <code>META_ACCESS_TOKEN</code> on the server, connect the Ad Account ID, then Sync to pull campaigns + daily spend/ROAS/CPA into the dashboard.</p>
          </CardContent>
        </Card>

        {/* Bulk import — Meta Ads Manager export */}
        <Card>
          <CardHeader><CardTitle>Bulk import — Meta export</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) { setImportMsg("Importing…"); importFile.mutate(f); } }}
              className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-lg file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-foreground"
            />
            {importMsg && <p className="text-xs text-muted-foreground">{importMsg}</p>}
            <p className="text-xs text-muted-foreground">Export from Meta Ads Manager with a <b>Day</b> column (daily metrics) and/or <b>Campaign name</b>, then drop the CSV/Excel here — columns are auto-detected.</p>
          </CardContent>
        </Card>

        {/* WooCommerce — orders */}
        <Card>
          <CardHeader className="flex-row items-center justify-between"><CardTitle>WooCommerce — Orders</CardTitle><Saved k="woo" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Store URL</Label><Input value={woo.url} onChange={(e) => setWoo({ ...woo, url: e.target.value })} placeholder="https://store.com" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Consumer key</Label><Input value={woo.key} onChange={(e) => setWoo({ ...woo, key: e.target.value })} placeholder="ck_…" /></div>
              <div className="space-y-1.5"><Label>Consumer secret</Label><Input type="password" value={woo.secret} onChange={(e) => setWoo({ ...woo, secret: e.target.value })} placeholder="cs_…" /></div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => connectWoo.mutate()} disabled={!woo.url || !woo.key || !woo.secret || connectWoo.isPending}>Connect</Button>
              <Button size="sm" onClick={() => { setWooMsg("Syncing…"); syncWoo.mutate(); }} disabled={syncWoo.isPending}>Sync orders</Button>
            </div>
            {wooMsg && <p className="text-xs text-muted-foreground">{wooMsg}</p>}
            <p className="text-xs text-muted-foreground">In WooCommerce → Settings → Advanced → REST API → Add key (Read permission). Paste the store URL + key/secret, Connect, then Sync to pull orders into the E-commerce tab.</p>
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
          <CardHeader className="flex-row items-center justify-between"><CardTitle>Create task / plan item</CardTitle><Saved k="task" /></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Title</Label><Input value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Priority</Label>
                <select value={task.priority} onChange={(e) => setTask({ ...task, priority: e.target.value })} className="h-11 w-full rounded-lg border border-input bg-background/60 px-3 text-sm">
                  <option>HIGH</option><option>MEDIUM</option><option>LOW</option>
                </select>
              </div>
              <div className="space-y-1.5"><Label>Timeframe</Label>
                <select value={task.timeframe} onChange={(e) => setTask({ ...task, timeframe: e.target.value })} className="h-11 w-full rounded-lg border border-input bg-background/60 px-3 text-sm">
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                </select>
              </div>
            </div>
            <div className="space-y-1.5"><Label>Responsible / detail</Label><Input value={task.responsible} onChange={(e) => setTask({ ...task, responsible: e.target.value })} placeholder="e.g. Creative team" /></div>
            <Button size="sm" onClick={() => addTask.mutate()} disabled={!task.title}>Add to plan</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
