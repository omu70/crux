"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LogIn, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { apiDelete, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@/components/ui";
import { useAccountManagers, useClients } from "@/lib/hooks";
import { formatCurrency } from "@/lib/utils";
import type { ClientRow } from "@/types";

const empty = {
  company_name: "", contact_name: "", username: "", password: "", email: "",
  plan: "Growth", monthly_budget: 0, monthly_target_revenue: 0, monthly_target_roas: 0,
  monthly_target_leads: 0, account_manager_id: "",
};

export default function ClientsPage() {
  const { data, isLoading } = useClients();
  const managers = useAccountManagers();
  const qc = useQueryClient();
  const router = useRouter();
  const { setToken } = useAuth();
  const [form, setForm] = useState(empty);
  const [showForm, setShowForm] = useState(false);
  const [err, setErr] = useState("");

  const create = useMutation({
    mutationFn: () => apiPost("/admin/clients", { ...form, account_manager_id: form.account_manager_id || null }),
    onSuccess: () => { setForm(empty); setShowForm(false); setErr(""); qc.invalidateQueries({ queryKey: ["admin-clients"] }); },
    onError: (e: any) => setErr(e.message),
  });
  const suspend = useMutation({ mutationFn: (id: string) => apiPost(`/admin/clients/${id}/suspend`), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-clients"] }) });
  const activate = useMutation({ mutationFn: (id: string) => apiPost(`/admin/clients/${id}/activate`), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-clients"] }) });
  const remove = useMutation({ mutationFn: (id: string) => apiDelete(`/admin/clients/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-clients"] }) });

  async function switchInto(id: string) {
    const r = await apiPost<{ access_token: string }>(`/admin/clients/${id}/switch`);
    await setToken(r.access_token);
    router.push("/dashboard");
  }

  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="space-y-6">
      <PageHeader title="Clients" subtitle="Create, manage and impersonate client accounts"
        action={<Button size="sm" onClick={() => setShowForm((v) => !v)}><Plus className="h-4 w-4" /> New client</Button>} />

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create client</CardTitle></CardHeader>
          <CardContent>
            {err && <div className="mb-3 rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-sm text-danger">{err}</div>}
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Company"><Input value={form.company_name} onChange={(e) => set("company_name", e.target.value)} /></Field>
              <Field label="Contact name"><Input value={form.contact_name} onChange={(e) => set("contact_name", e.target.value)} /></Field>
              <Field label="Username"><Input value={form.username} onChange={(e) => set("username", e.target.value)} /></Field>
              <Field label="Email"><Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} /></Field>
              <Field label="Password"><Input type="text" value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="min 8 chars" /></Field>
              <Field label="Plan"><Input value={form.plan} onChange={(e) => set("plan", e.target.value)} /></Field>
              <Field label="Monthly budget"><Input type="number" value={form.monthly_budget} onChange={(e) => set("monthly_budget", +e.target.value)} /></Field>
              <Field label="Target revenue"><Input type="number" value={form.monthly_target_revenue} onChange={(e) => set("monthly_target_revenue", +e.target.value)} /></Field>
              <Field label="Target ROAS"><Input type="number" value={form.monthly_target_roas} onChange={(e) => set("monthly_target_roas", +e.target.value)} /></Field>
              <Field label="Target leads"><Input type="number" value={form.monthly_target_leads} onChange={(e) => set("monthly_target_leads", +e.target.value)} /></Field>
              <Field label="Account manager">
                <select value={form.account_manager_id} onChange={(e) => set("account_manager_id", e.target.value)}
                  className="h-11 w-full rounded-lg border border-input bg-background/60 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                  <option value="">Unassigned</option>
                  {(managers.data ?? []).map((m: any) => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </Field>
            </div>
            <div className="mt-4 flex gap-2">
              <Button size="sm" onClick={() => create.mutate()} disabled={create.isPending}>Create client</Button>
              <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? <Loading /> : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="p-4 font-medium">Company</th>
                    <th className="p-4 font-medium">Plan</th>
                    <th className="p-4 font-medium">Status</th>
                    <th className="p-4 text-right font-medium">Budget</th>
                    <th className="p-4 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(data ?? []).map((c: ClientRow) => (
                    <tr key={c.id} className="border-b border-border/60 last:border-0">
                      <td className="p-4">
                        <Link href={`/admin/clients/${c.id}`} className="font-medium hover:text-primary">{c.company_name}</Link>
                        <div className="text-xs text-muted-foreground">{c.contact_name}</div>
                      </td>
                      <td className="p-4"><Badge tone="primary">{c.plan}</Badge></td>
                      <td className="p-4"><Badge tone={c.status === "ACTIVE" ? "success" : "warning"}>{c.status}</Badge></td>
                      <td className="p-4 text-right tabular">{formatCurrency(c.monthly_budget)}</td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button size="sm" variant="outline" onClick={() => switchInto(c.id)}><LogIn className="h-3.5 w-3.5" /> Enter</Button>
                          {c.status === "ACTIVE"
                            ? <Button size="sm" variant="ghost" onClick={() => suspend.mutate(c.id)}>Suspend</Button>
                            : <Button size="sm" variant="ghost" onClick={() => activate.mutate(c.id)}>Activate</Button>}
                          <Button size="icon" variant="ghost" onClick={() => confirm(`Delete ${c.company_name}?`) && remove.mutate(c.id)}><Trash2 className="h-4 w-4 text-danger" /></Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-1.5"><Label>{label}</Label>{children}</div>;
}
