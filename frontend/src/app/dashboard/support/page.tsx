"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Send } from "lucide-react";
import { useState } from "react";
import { EmptyState, Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { apiGet, apiPost } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@/components/ui";
import { useTickets } from "@/lib/hooks";

const statusTone: Record<string, "success" | "warning" | "primary" | "default"> = {
  OPEN: "warning", IN_PROGRESS: "primary", RESOLVED: "success", CLOSED: "default",
};

export default function SupportPage() {
  const { data, isLoading } = useTickets();
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [subject, setSubject] = useState("");
  const [desc, setDesc] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [reply, setReply] = useState("");

  const detail = useQuery({ queryKey: ["ticket", openId], queryFn: () => apiGet(`/tickets/${openId}`), enabled: !!openId });

  const create = useMutation({
    mutationFn: () => apiPost("/tickets", { subject, description: desc, priority: "MEDIUM" }),
    onSuccess: () => { setSubject(""); setDesc(""); setCreating(false); qc.invalidateQueries({ queryKey: ["tickets"] }); },
  });
  const sendReply = useMutation({
    mutationFn: () => apiPost(`/tickets/${openId}/reply`, { body: reply }),
    onSuccess: () => { setReply(""); qc.invalidateQueries({ queryKey: ["ticket", openId] }); qc.invalidateQueries({ queryKey: ["tickets"] }); },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Support" subtitle="Raise a ticket and track its status" action={<Button size="sm" onClick={() => setCreating((v) => !v)}><Plus className="h-4 w-4" /> New ticket</Button>} />

      {creating && (
        <Card>
          <CardContent className="space-y-3 p-5">
            <div className="space-y-1.5"><Label>Subject</Label><Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Brief summary" /></div>
            <div className="space-y-1.5"><Label>Description</Label>
              <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={3} placeholder="Describe your issue…"
                className="w-full rounded-lg border border-input bg-background/60 p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
            </div>
            <Button size="sm" onClick={() => create.mutate()} disabled={!subject || !desc || create.isPending}>Submit ticket</Button>
          </CardContent>
        </Card>
      )}

      {isLoading ? <Loading /> :
        (data ?? []).length === 0 ? <EmptyState title="No tickets yet" desc="Raise a ticket and our team will respond." /> : (
          <div className="grid gap-3">
            {(data ?? []).map((t: any) => (
              <Card key={t.id} className="cursor-pointer p-4 transition-colors hover:border-primary/40" onClick={() => setOpenId(t.id)}>
                <div className="flex items-center justify-between">
                  <div className="font-medium">{t.subject}</div>
                  <Badge tone={statusTone[t.status]}>{t.status.replace("_", " ")}</Badge>
                </div>
                <div className="mt-1 line-clamp-1 text-sm text-muted-foreground">{t.description}</div>
              </Card>
            ))}
          </div>
        )}

      {openId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setOpenId(null)}>
          <Card className="flex max-h-[85vh] w-full max-w-lg flex-col" onClick={(e) => e.stopPropagation()}>
            <CardHeader><CardTitle className="text-foreground">{detail.data?.subject ?? "Ticket"}</CardTitle></CardHeader>
            <CardContent className="flex-1 space-y-3 overflow-y-auto">
              {(detail.data?.messages ?? []).map((m: any) => (
                <div key={m.id} className="rounded-lg border border-border p-3 text-sm">{m.body}</div>
              ))}
            </CardContent>
            <div className="flex gap-2 border-t border-border p-3">
              <Input value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Write a reply…" onKeyDown={(e) => e.key === "Enter" && reply && sendReply.mutate()} />
              <Button size="icon" onClick={() => sendReply.mutate()} disabled={!reply}><Send className="h-4 w-4" /></Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
