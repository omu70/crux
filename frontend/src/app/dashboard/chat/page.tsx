"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { apiPost } from "@/lib/api";
import { Button, Card, Input } from "@/components/ui";
import { useChat } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const { data, isLoading } = useChat();
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const send = useMutation({
    mutationFn: () => apiPost("/chat", { body: text }),
    onSuccess: () => { setText(""); qc.invalidateQueries({ queryKey: ["chat"] }); },
  });

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [data]);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <PageHeader title="Messages" subtitle="Chat directly with your DiziGroww team" />
      <Card className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-3 overflow-y-auto p-5">
          {isLoading ? <Loading /> : (data ?? []).map((m: any) => {
            const mine = m.sender_role === "CLIENT";
            return (
              <div key={m.id} className={cn("flex", mine ? "justify-end" : "justify-start")}>
                <div className={cn("max-w-[75%] rounded-2xl px-4 py-2 text-sm", mine ? "bg-primary text-primary-foreground" : "border border-border bg-card")}>
                  {m.body}
                  <div className={cn("mt-1 text-[10px]", mine ? "text-primary-foreground/70" : "text-muted-foreground")}>
                    {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>
              </div>
            );
          })}
          <div ref={endRef} />
        </div>
        <div className="flex gap-2 border-t border-border p-3">
          <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="Type a message…" onKeyDown={(e) => e.key === "Enter" && text && send.mutate()} />
          <Button size="icon" onClick={() => send.mutate()} disabled={!text}><Send className="h-4 w-4" /></Button>
        </div>
      </Card>
    </div>
  );
}
