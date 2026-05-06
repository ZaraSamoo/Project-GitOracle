"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AppHeader } from "@/components/app-header";
import { LeadsTable } from "@/components/ui/leads-data-table";
import { getSessionToken, getSessionUserId } from "@/lib/auth-session";
import { flaskRequest } from "@/lib/flask-api";
import type { TrendingRepo } from "@/lib/github-trending";

interface RepositoryResponse {
  saved_projects: Array<{
    repo_id: number;
    full_name: string;
    description: string | null;
    owner: string;
    language: string | null;
    stars: number;
    forks: number;
    html_url: string | null;
  }>;
}

const savedRepoCache = new Map<number, RepositoryResponse["saved_projects"]>();

export default function SavedProjectsPage() {
  const [repositories, setRepositories] = useState<RepositoryResponse["saved_projects"]>([]);
  const [completedRepositories, setCompletedRepositories] = useState<RepositoryResponse["saved_projects"]>([]);
  const [repositoriesError, setRepositoriesError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  const userId = useMemo(() => getSessionUserId(), []);
  const token = useMemo(() => getSessionToken(), []);
  const needsSignup = !userId;

  useEffect(() => {
    let isCancelled = false;

    async function fetchSavedRepos() {
      if (!userId) {
        setLoading(false);
        return;
      }
      const cached = savedRepoCache.get(userId);
      if (cached) {
        setRepositories(cached);
        setRepositoriesError(undefined);
        setLoading(false);
        return;
      }

      try {
        const [data, completed] = await Promise.all([
          flaskRequest<RepositoryResponse>({
            path: `/api/saved-repos?user_id=${userId}`,
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          }),
          flaskRequest<{ completed_projects: RepositoryResponse["saved_projects"] }>({
            path: `/api/completed-repos?user_id=${userId}`,
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          }),
        ]);
        const sliced = data.saved_projects.slice(0, 50);
        savedRepoCache.set(userId, sliced);

        if (!isCancelled) {
          setRepositories(sliced);
          setCompletedRepositories(completed.completed_projects.slice(0, 50));
          setRepositoriesError(undefined);
        }
      } catch (error) {
        if (!isCancelled) {
          setRepositories([]);
          setRepositoriesError(
            error instanceof Error ? error.message : "Failed to fetch saved projects from Flask."
          );
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    fetchSavedRepos();

    return () => {
      isCancelled = true;
    };
  }, [userId, token]);

  const toTrending = (items: RepositoryResponse["saved_projects"]): TrendingRepo[] =>
    items.map((repo) => ({
      id: String(repo.repo_id),
      name: repo.full_name,
      owner: repo.owner || "unknown",
      url: repo.html_url || "#",
      stars: repo.stars || 0,
      forks: repo.forks || 0,
      openIssues: 0,
      watchers: Math.max(1, Math.round((repo.stars || 0) * 0.25)),
      sizeKb: Math.max(100, (repo.stars || 1) * 2),
      contributors: 1,
      pullRequests: 0,
      commitActivity: "Medium",
      languages: [repo.language || "Unknown"],
      difficulty: "medium",
    }));

  const markCompleted = async (repo: TrendingRepo) => {
    if (!userId) return;
    try {
      await flaskRequest({
        path: "/api/saved-repos/complete",
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: JSON.stringify({ repo_id: Number(repo.id), user_id: userId }),
      });
      setRepositories((current) => current.filter((r) => String(r.repo_id) !== repo.id));
      const moved = repositories.find((r) => String(r.repo_id) === repo.id);
      if (moved) setCompletedRepositories((current) => [moved, ...current]);
    } catch (error) {
      setRepositoriesError(error instanceof Error ? error.message : "Failed to mark repository completed.");
    }
  };

  if (needsSignup) {
    return (
      <div className="min-h-screen bg-black text-white">
        <AppHeader />
        <main className="mx-auto flex max-w-3xl flex-col items-center justify-center px-4 py-20 text-center">
          <h1 className="text-2xl font-semibold md:text-3xl">Sign up first</h1>
          <p className="mt-2 text-sm text-zinc-400">Save projects after creating an account.</p>
          <Link href="/create-account" className="mt-6 rounded-full border border-white/20 px-5 py-2 text-sm hover:bg-white/10">
            Create Account
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-bold md:text-5xl">Saved Projects</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">Move projects from saved to completed as you finish them.</p>
        {loading ? <p className="mt-4 text-sm text-zinc-300">Loading your saved repositories...</p> : null}
        {repositoriesError ? <p className="mt-4 text-sm text-rose-300">{repositoriesError}</p> : null}
        {!loading && !repositoriesError ? (
          <section className="mt-6">
            <LeadsTable
              title="Saved Repositories"
              leads={toTrending(repositories)}
              primaryActionLabel="Mark Completed"
              onPrimaryAction={markCompleted}
            />
          </section>
        ) : null}
        {!loading && !repositoriesError ? (
          <section className="mt-8">
            <LeadsTable title="Completed Repositories" leads={toTrending(completedRepositories)} />
          </section>
        ) : null}
      </main>
    </div>
  );
}
