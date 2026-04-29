import { AppHeader } from "@/components/app-header";
import { LeadsTable } from "@/components/ui/leads-data-table";
import { TrendingAreaChart } from "@/components/ui/trending-area-chart";
import { getTrendingRepos } from "@/lib/github-trending";

export default async function TrendingProjectsPage() {
  const repos = await getTrendingRepos();

  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-bold md:text-5xl">Trending Projects</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          Real-time GitHub trending intelligence with repo metrics and quick-read difficulty tags:
          low, medium, amateur, and high.
        </p>
        <section className="mt-8">
          <TrendingAreaChart repos={repos} />
        </section>
        <section className="mt-6">
          <LeadsTable leads={repos} />
        </section>
      </main>
    </div>
  );
}
