"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { apiPatch } from "@/lib/api";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useTasks } from "@/lib/hooks";

const columns: { key: string; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "in_progress", label: "In Progress" },
  { key: "completed", label: "Completed" },
];
const prioTone: Record<string, "danger" | "warning" | "default"> = { HIGH: "danger", MEDIUM: "warning", LOW: "default" };
const next: Record<string, string> = { PENDING: "IN_PROGRESS", IN_PROGRESS: "COMPLETED", COMPLETED: "PENDING" };

export default function TasksPage() {
  const { data, isLoading } = useTasks();
  const qc = useQueryClient();
  const mutate = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiPatch(`/tasks/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  if (isLoading) return <Loading />;
  const buckets = data?.buckets ?? { pending: [], in_progress: [], completed: [] };

  return (
    <div className="space-y-6">
      <PageHeader title="Task Tracker" subtitle="What we're working on for you, in real time" />
      <div className="grid gap-4 lg:grid-cols-3">
        {columns.map((col) => (
          <Card key={col.key}>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>{col.label}</CardTitle>
              <Badge>{(buckets as any)[col.key].length}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {(buckets as any)[col.key].map((t: any) => (
                <div key={t.id} className="rounded-lg border border-border p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-medium">{t.title}</div>
                    <Badge tone={prioTone[t.priority]}>{t.priority}</Badge>
                  </div>
                  {t.responsible && <div className="mt-1 text-xs text-muted-foreground">{t.responsible}</div>}
                  {t.expected_result && <div className="mt-1 text-xs text-muted-foreground">{t.expected_result}</div>}
                  <button
                    onClick={() => mutate.mutate({ id: t.id, status: next[t.status] })}
                    className="mt-2 text-xs font-medium text-primary hover:underline"
                  >
                    Move to {next[t.status].replace("_", " ").toLowerCase()} →
                  </button>
                </div>
              ))}
              {(buckets as any)[col.key].length === 0 && <p className="py-6 text-center text-xs text-muted-foreground">Nothing here</p>}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
