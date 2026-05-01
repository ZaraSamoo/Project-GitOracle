"use client";

import { useEffect, useMemo, useState } from "react";
import { ProjectPageTemplate } from "@/components/project-page-template";
import { getSessionToken, getSessionUserId } from "@/lib/auth-session";
import { flaskRequest } from "@/lib/flask-api";

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
  const [repositoriesError, setRepositoriesError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  const userId = useMemo(() => getSessionUserId(), []);
  const token = useMemo(() => getSessionToken(), []);

  useEffect(() => {
    let isCancelled = false;

    async function fetchSavedRepos() {
      if (!userId) {
        setRepositories([]);
        setRepositoriesError("Please sign in to view your saved repositories.");
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
        const data = await flaskRequest<RepositoryResponse>({
          path: `/api/saved-repos?user_id=${userId}`,
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        const sliced = data.saved_projects.slice(0, 50);
        savedRepoCache.set(userId, sliced);

        if (!isCancelled) {
          setRepositories(sliced);
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

  return (
    <ProjectPageTemplate
      title="Saved Projects"
      subtitle="Keep your shortlisted repositories in one place and compare time estimates so you can decide what to build next."
      imageUrl="https://images.unsplash.com/photo-1484417894907-623942c8ee29?auto=format&fit=crop&w=1600&q=80"
      repositories={repositories}
      repositoriesError={repositoriesError}
      loading={loading}
      emptyMessage="You haven't saved any repositories yet."
    />
  );
}
