"use client";

import { AlertTriangle } from "lucide-react";
import { EmptyState, Loading, StatTile } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { useEcommerce } from "@/lib/hooks";
import { formatCurrency, formatNumber } from "@/lib/utils";

const orderTone: Record<string, "success" | "warning" | "danger" | "default"> = {
  PAID: "success", CANCELLED: "warning", REFUNDED: "danger", PENDING: "default",
};

export default function EcommercePage() {
  const { data, isLoading } = useEcommerce();
  if (isLoading) return <Loading />;
  const d = data ?? {};

  return (
    <div className="space-y-6">
      <PageHeader title="E-commerce" subtitle="Orders & revenue from Shopify / WooCommerce" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatTile label="Orders" value={formatNumber(d.orders ?? 0)} />
        <StatTile label="Revenue" value={formatCurrency(d.revenue ?? 0)} />
        <StatTile label="AOV" value={formatCurrency(d.aov ?? 0)} />
        <StatTile label="Cancelled" value={d.cancelled ?? 0} />
        <StatTile label="Refunds" value={d.refunds ?? 0} />
        <StatTile label="Low Stock" value={(d.inventory_alerts ?? []).length} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Top Products</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(d.top_products ?? []).map((p: any) => (
              <div key={p.title} className="flex items-center justify-between text-sm">
                <span>{p.title}</span>
                <span className="tabular text-muted-foreground">{formatCurrency(p.revenue)} · {p.units_sold} sold</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Top Categories</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(d.top_categories ?? []).map((cat: any) => (
              <div key={cat.category} className="flex items-center justify-between text-sm">
                <span>{cat.category}</span>
                <span className="tabular text-muted-foreground">{formatCurrency(cat.revenue)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {(d.inventory_alerts ?? []).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-warning" /> Inventory Alerts</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(d.inventory_alerts ?? []).map((p: any) => (
              <Badge key={p.title} tone="warning">{p.title} · {p.inventory} left</Badge>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Recent Orders</CardTitle></CardHeader>
        <CardContent>
          {(d.recent_orders ?? []).length === 0 ? <EmptyState title="No orders yet" /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Order</th>
                    <th className="pb-2 pr-4 font-medium">Date</th>
                    <th className="pb-2 pr-4 font-medium">Customer</th>
                    <th className="pb-2 pr-4 text-right font-medium">Total</th>
                    <th className="pb-2 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="tabular">
                  {(d.recent_orders ?? []).map((o: any) => (
                    <tr key={o.order_number} className="border-b border-border/60 last:border-0">
                      <td className="py-2.5 pr-4 font-medium">{o.order_number}</td>
                      <td className="py-2.5 pr-4 text-muted-foreground">{o.created_at ? new Date(o.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}</td>
                      <td className="py-2.5 pr-4">{o.customer_name}</td>
                      <td className="py-2.5 pr-4 text-right">{formatCurrency(o.total)}</td>
                      <td className="py-2.5 text-right"><Badge tone={orderTone[o.status]}>{o.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
