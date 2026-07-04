"use client";

import { FileArchive, FileImage, FileText, FileVideo, File as FileIcon, Download } from "lucide-react";
import { EmptyState, Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent } from "@/components/ui";
import { useDocuments } from "@/lib/hooks";

const catTone: Record<string, "primary" | "success" | "warning" | "default"> = {
  INVOICE: "warning", REPORT: "primary", CREATIVE: "success", CONTRACT: "default", OTHER: "default",
};
function iconFor(type: string) {
  if (["png", "jpg", "jpeg", "gif", "webp"].includes(type)) return FileImage;
  if (["mp4", "mov", "webm"].includes(type)) return FileVideo;
  if (["zip", "rar"].includes(type)) return FileArchive;
  if (["pdf", "doc", "docx"].includes(type)) return FileText;
  return FileIcon;
}
function fmtSize(b: number) {
  if (b > 1e6) return `${(b / 1e6).toFixed(1)} MB`;
  if (b > 1e3) return `${(b / 1e3).toFixed(0)} KB`;
  return `${b} B`;
}

export default function DocumentsPage() {
  const { data, isLoading } = useDocuments();
  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6">
      <PageHeader title="Document Center" subtitle="Invoices, reports, creatives and contracts" />
      {(data ?? []).length === 0 ? <EmptyState title="No documents yet" /> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(data ?? []).map((d: any) => {
            const Icon = iconFor(d.file_type);
            return (
              <Card key={d.id} className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground"><Icon className="h-5 w-5" /></div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{d.name}</div>
                    <div className="mt-0.5 text-xs text-muted-foreground">{fmtSize(d.size_bytes)}</div>
                  </div>
                  <a href={d.file_url} target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-primary"><Download className="h-4 w-4" /></a>
                </div>
                <div className="mt-3"><Badge tone={catTone[d.category]}>{d.category}</Badge></div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
