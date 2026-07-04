"use client";

import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { cn } from "@/lib/utils";

export const RANGES: { key: string; label: string }[] = [
  { key: "today", label: "Today" },
  { key: "yesterday", label: "Yesterday" },
  { key: "7d", label: "7 Days" },
  { key: "30d", label: "30 Days" },
  { key: "last_month", label: "Last Month" },
  { key: "quarter", label: "Quarter" },
];

export function RangeSelector({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="inline-flex flex-wrap gap-1 rounded-lg border border-border bg-card/60 p-1">
      {RANGES.map((r) => (
        <button
          key={r.key}
          onClick={() => onChange(r.key)}
          className={cn(
            "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
            value === r.key ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

const AXIS = "hsl(var(--muted-foreground))";
const GRID = "hsl(var(--border))";

function fmtDate(d: string) {
  const dt = new Date(d);
  return `${dt.getMonth() + 1}/${dt.getDate()}`;
}

function TooltipBox({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 text-xs shadow-soft">
      <div className="mb-1 font-medium text-muted-foreground">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2 tabular">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="capitalize text-muted-foreground">{p.name}:</span>
          <span className="font-medium">{typeof p.value === "number" ? p.value.toLocaleString() : p.value}</span>
        </div>
      ))}
    </div>
  );
}

export function AreaTrend({
  title, data, dataKey, color = "hsl(var(--primary))", height = 260,
}: { title: string; data: any[]; dataKey: string; color?: string; height?: number }) {
  const id = `grad-${dataKey}`;
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ left: -18, right: 6, top: 4 }}>
            <defs>
              <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke={GRID} strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={fmtDate} stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} minTickGap={24} />
            <YAxis stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} width={48} />
            <Tooltip content={<TooltipBox />} />
            <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#${id})`} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function MultiLine({
  title, data, keys, height = 260,
}: { title: string; data: any[]; keys: { key: string; color: string }[]; height?: number }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ left: -18, right: 6, top: 4 }}>
            <CartesianGrid vertical={false} stroke={GRID} strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={fmtDate} stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} minTickGap={24} />
            <YAxis stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} width={48} />
            <Tooltip content={<TooltipBox />} />
            {keys.map((k) => (
              <Line key={k.key} type="monotone" dataKey={k.key} stroke={k.color} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function BarSeries({
  title, data, dataKey, color = "hsl(var(--primary))", height = 260,
}: { title: string; data: any[]; dataKey: string; color?: string; height?: number }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} margin={{ left: -18, right: 6, top: 4 }}>
            <CartesianGrid vertical={false} stroke={GRID} strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={fmtDate} stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} minTickGap={24} />
            <YAxis stroke={AXIS} fontSize={11} tickLine={false} axisLine={false} width={48} />
            <Tooltip content={<TooltipBox />} cursor={{ fill: "hsl(var(--muted) / 0.4)" }} />
            <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

const DONUT = ["hsl(var(--primary))", "hsl(var(--accent))", "hsl(200 90% 60%)", "hsl(152 60% 45%)", "hsl(38 92% 55%)"];

export function Donut({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={230}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={54} outerRadius={82} paddingAngle={3} stroke="none">
              {data.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
            </Pie>
            <Tooltip content={<TooltipBox />} />
            <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
