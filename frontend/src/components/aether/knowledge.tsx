"use client";

import { FileUp, Library, SearchIcon } from "lucide-react";
import { useRef, useState } from "react";
import {
  Chip, ErrorNote, GlassCard, ScoreBar, SectionHeader, timeAgo,
} from "@/components/aether/shared";
import { Badge, Button, Input, Skeleton } from "@/components/ui";
import { useKnowledgeDocs, useKnowledgeSearch, useUploadKnowledge } from "@/lib/aether";

export function KnowledgeBase() {
  const docs = useKnowledgeDocs();
  const upload = useUploadKnowledge();
  const search = useKnowledgeSearch();
  const fileRef = useRef<HTMLInputElement>(null);
  const [namespace, setNamespace] = useState("business");
  const [query, setQuery] = useState("");

  const runSearch = () => {
    if (query.trim()) search.mutate({ query: query.trim(), k: 6 });
  };

  return (
    <div>
      <SectionHeader
        title="Knowledge Base"
        desc="Feed Aether documents — briefs, reviews, transcripts — and search them semantically."
        icon={Library}
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Upload + documents */}
        <GlassCard className="p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              placeholder="namespace (e.g. business)"
              className="h-9 max-w-[180px] text-xs"
            />
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload.mutate({ file: f, namespace: namespace || "business" });
                e.target.value = "";
              }}
            />
            <Button size="sm" variant="outline" disabled={upload.isPending} onClick={() => fileRef.current?.click()}>
              <FileUp className="h-3.5 w-3.5" />
              {upload.isPending ? "Uploading…" : "Upload document"}
            </Button>
          </div>
          <ErrorNote error={upload.error ?? undefined} />
          {upload.data && (
            <div className="mt-2 text-xs text-success">
              Indexed "{upload.data.title}" into {upload.data.chunks ?? 0} chunks.
            </div>
          )}
          <div className="mt-4 space-y-2">
            {docs.isLoading && <Skeleton className="h-16" />}
            {!docs.isLoading && !(docs.data ?? []).length && (
              <div className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
                No documents yet. Upload PDFs, docs or text to give Aether long-term memory.
              </div>
            )}
            {(docs.data ?? []).map((d) => (
              <div key={d.id} className="flex items-center justify-between gap-2 rounded-lg border border-border/60 px-3 py-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{d.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {d.source_type ?? "file"} · {timeAgo(d.created_at)}
                  </div>
                </div>
                <Badge>{d.namespace ?? "default"}</Badge>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Semantic search */}
        <GlassCard className="p-5">
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              placeholder="Ask your knowledge base anything…"
              className="h-9 text-xs"
            />
            <Button size="sm" disabled={search.isPending || !query.trim()} onClick={runSearch}>
              <SearchIcon className="h-3.5 w-3.5" />
              {search.isPending ? "Searching…" : "Search"}
            </Button>
          </div>
          <ErrorNote error={search.error ?? undefined} />
          <div className="mt-4 space-y-2">
            {search.isPending && <Skeleton className="h-20" />}
            {search.data?.length === 0 && <div className="text-xs text-muted-foreground">No matches found.</div>}
            {(search.data ?? []).map((h, i) => (
              <div key={i} className="rounded-lg border border-border/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="truncate text-xs font-medium">{h.title ?? "Untitled"}</div>
                  <Chip tone="violet">{(h.score * 100).toFixed(0)}% match</Chip>
                </div>
                <p className="mt-1.5 line-clamp-4 text-xs leading-relaxed text-muted-foreground">{h.content}</p>
                <ScoreBar value={h.score * 100} className="mt-2" />
              </div>
            ))}
            {!search.data && !search.isPending && (
              <div className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
                Semantic search runs across every indexed chunk — try "what do customers complain about?"
              </div>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
