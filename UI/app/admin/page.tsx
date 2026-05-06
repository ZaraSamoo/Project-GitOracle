"use client";

import { useEffect, useMemo, useState } from "react";
import { Pie, PieChart, Cell } from "recharts";
import { AppHeader } from "@/components/app-header";
import { WebGLShader } from "@/components/ui/webgl-shader";
import { getSessionRole, getSessionToken } from "@/lib/auth-session";
import { flaskRequest } from "@/lib/flask-api";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/area-charts-2";

type AdminData = {
  summary: {
    total_users: number;
    total_repositories: number;
    total_saved_projects: number;
    open_issues: number;
    closed_issues: number;
  };
  languages: Array<{ name: string; count: number }>;
  top_repositories: Array<{
    repo_id: number;
    full_name: string;
    language: string | null;
    stars: number;
    forks: number;
    html_url: string | null;
  }>;
  newest_users: Array<{
    user_id: number;
    username: string;
    email: string;
    created_at: string | null;
  }>;
};

const PIE_COLORS = ["#8b5cf6", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#6366f1", "#ec4899", "#14b8a6"];
const chartConfig = {
  count: { label: "Repositories", color: "var(--color-violet-500)" },
} satisfies ChartConfig;

export default function AdminPage() {
  const [data, setData] = useState<AdminData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const role = useMemo(() => getSessionRole(), []);
  const token = useMemo(() => getSessionToken(), []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (role !== "admin" || !token) {
        if (!cancelled) {
          setError("Admin access only. Sign in as admin.");
          setLoading(false);
        }
        return;
      }

      try {
        const response = await flaskRequest<AdminData>({
          path: "/api/admin/overview",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!cancelled) {
          setData(response);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Failed to load admin data.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [role, token]);

  return (
    <div className="relative min-h-screen bg-black text-white">
      <WebGLShader />
      <div className="relative z-10">
        <AppHeader />
        <main className="mx-auto max-w-6xl px-4 py-8">
          <h1 className="text-3xl font-bold md:text-5xl">Admin Portal</h1>
          <p className="mt-2 text-sm text-zinc-300">Live system metrics from Flask database endpoints.</p>

          {loading && <p className="mt-8 text-zinc-300">Loading admin analytics...</p>}
          {error && !loading && <p className="mt-8 rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-rose-200">{error}</p>}

          {!loading && !error && data && (
            <>
              <section className="mt-8 grid gap-4 md:grid-cols-5">
                <StatCard label="Users" value={data.summary.total_users} />
                <StatCard label="Repositories" value={data.summary.total_repositories} />
                <StatCard label="Saved Projects" value={data.summary.total_saved_projects} />
                <StatCard label="Open Issues" value={data.summary.open_issues} />
                <StatCard label="Closed Issues" value={data.summary.closed_issues} />
              </section>

              <section className="mt-8 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/15 bg-black/45 p-4 backdrop-blur">
                  <h2 className="text-lg font-semibold">Language Distribution</h2>
                  <p className="mt-1 text-xs text-zinc-400">Top languages across indexed repositories.</p>
                  <div className="mt-4 h-72">
                    <ChartContainer config={chartConfig} className="h-full w-full">
                      <PieChart>
                        <Pie data={data.languages} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={95} label>
                          {data.languages.map((entry, index) => (
                            <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <ChartTooltip content={<ChartTooltipContent />} />
                      </PieChart>
                    </ChartContainer>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/15 bg-black/45 p-4 backdrop-blur">
                  <h2 className="text-lg font-semibold">Newest Users</h2>
                  <p className="mt-1 text-xs text-zinc-400">Latest accounts from your live user table.</p>
                  <div className="mt-4 space-y-2">
                    {data.newest_users.map((user) => (
                      <div key={user.user_id} className="rounded-lg border border-white/10 bg-black/35 p-3">
                        <div className="font-medium">{user.username}</div>
                        <div className="text-xs text-zinc-400">{user.email}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="mt-8 rounded-2xl border border-white/15 bg-black/45 p-4 backdrop-blur">
                <h2 className="text-lg font-semibold">Top Repositories</h2>
                <p className="mt-1 text-xs text-zinc-400">Highest-star repositories from the database.</p>
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-left text-zinc-400">
                        <th className="py-2 pr-3">Repository</th>
                        <th className="py-2 pr-3">Language</th>
                        <th className="py-2 pr-3">Stars</th>
                        <th className="py-2 pr-3">Forks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_repositories.map((repo) => (
                        <tr key={repo.repo_id} className="border-b border-white/5">
                          <td className="py-2 pr-3">
                            {repo.html_url ? (
                              <a href={repo.html_url} target="_blank" rel="noreferrer" className="text-cyan-300 hover:underline">
                                {repo.full_name}
                              </a>
                            ) : (
                              repo.full_name
                            )}
                          </td>
                          <td className="py-2 pr-3">{repo.language ?? "Unknown"}</td>
                          <td className="py-2 pr-3">{repo.stars.toLocaleString()}</td>
                          <td className="py-2 pr-3">{repo.forks.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-white/15 bg-black/45 p-4 backdrop-blur">
      <div className="text-xs uppercase tracking-wider text-zinc-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value.toLocaleString()}</div>
    </div>
  );
}
