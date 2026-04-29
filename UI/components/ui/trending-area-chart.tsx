"use client";

import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import type { TrendingRepo } from "@/lib/github-trending";
import { Card, CardContent, CardHeader, CardTitle, CardToolbar } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/area-charts-2";

type MetricKey = "stars" | "forks" | "watchers" | "openIssues";

const metricOptions: { key: MetricKey; label: string }[] = [
  { key: "stars", label: "Stars" },
  { key: "forks", label: "Forks" },
  { key: "watchers", label: "Watchers" },
  { key: "openIssues", label: "Open Issues" },
];

const chartConfig = {
  selectedMetric: { label: "Selected Metric", color: "var(--color-violet-500)" },
} satisfies ChartConfig;

export function TrendingAreaChart({ repos }: { repos: TrendingRepo[] }) {
  const [metric, setMetric] = useState<MetricKey>("stars");
  const chartData = useMemo(
    () =>
      repos.map((repo) => ({
        name: repo.name.split("/")[1] || repo.name,
        selectedMetric: repo[metric] as number,
      })),
    [repos, metric]
  );

  return (
    <Card className="border-white/10 bg-zinc-950/60">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg text-white">Trending Metrics Graph</CardTitle>
        <CardToolbar>
          <Select value={metric} onValueChange={(value) => setMetric(value as MetricKey)}>
            <SelectTrigger className="w-44 border-white/15 bg-black text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {metricOptions.map((option) => (
                <SelectItem key={option.key} value={option.key}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardToolbar>
      </CardHeader>
      <CardContent className="pt-2">
        <ChartContainer config={chartConfig} className="relative h-[320px] w-full min-w-0">
          <AreaChart data={chartData} margin={{ top: 10, right: 16, left: 16, bottom: 10 }}>
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey="name" tickLine={false} axisLine={false} tickMargin={10} stroke="#a1a1aa" />
            <YAxis tickLine={false} axisLine={false} stroke="#a1a1aa" />
            <ChartTooltip content={<ChartTooltipContent />} />
            <defs>
              <linearGradient id="selectedMetricFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-selectedMetric)" stopOpacity={0.5} />
                <stop offset="95%" stopColor="var(--color-selectedMetric)" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <Area
              dataKey="selectedMetric"
              type="natural"
              stroke="var(--color-selectedMetric)"
              fill="url(#selectedMetricFill)"
              fillOpacity={1}
              strokeWidth={2}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
