"use client";

import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { PromptInputBox } from "@/components/ui/ai-prompt-box";
import { flaskRequest } from "@/lib/flask-api";

interface SearchResponse {
  count: number;
  results: Array<{
    repo_id: number;
    full_name: string;
    description: string | null;
    stars: number;
    language: string | null;
    html_url: string | null;
  }>;
}

export default function FindProjectsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<SearchResponse["results"]>([]);
  const [query, setQuery] = useState("");

  const searchProjects = async (rawQuery: string) => {
    const trimmedQuery = rawQuery.trim();
    if (!trimmedQuery) {
      setProjects([]);
      setError("Please type a search term.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await flaskRequest<SearchResponse>({
        path: `/api/search?q=${encodeURIComponent(trimmedQuery)}`,
        timeoutMs: 4000,
      });
      setProjects(data.results);
      setQuery(trimmedQuery);
    } catch (requestError) {
      setProjects([]);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to fetch search results from Flask API."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-bold md:text-5xl">Find Projects</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">
          Describe your domain and free hours, then generate project prompts tailored to your
          learning path and current skill level.
        </p>

        <section className="mt-8 rounded-3xl border border-white/10 bg-gradient-to-br from-zinc-950 via-violet-950/20 to-cyan-950/20 p-5 md:p-8">
          <div className="mx-auto max-w-3xl">
            <PromptInputBox
              placeholder="Search repositories by name or description (e.g. react, flask, machine learning)"
              isLoading={isLoading}
              onSend={async (message, files) => {
                // PromptInputBox already prevents default Enter submit in its key handler.
                console.log("Find Projects search:", message, files);
                await searchProjects(message);
              }}
            />
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-white/10 bg-zinc-950/60 p-5 md:p-8">
          <h2 className="text-xl font-semibold">Database Search Results</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Searches your Flask `repositories` table via `/api/search`.
          </p>
          {isLoading && <p className="mt-4 text-sm text-cyan-300">Loading results...</p>}
          {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
          {!error && !isLoading && projects.length === 0 && (
            <p className="mt-4 text-sm text-zinc-400">
              Enter a query and press Enter to search your database.
            </p>
          )}
          {!isLoading && projects.length > 0 && (
            <ul className="mt-4 space-y-2 text-sm">
              {projects.map((project) => (
                <li
                  key={project.repo_id}
                  className="rounded-xl border border-white/10 bg-black/30 px-4 py-3"
                >
                  <p className="font-medium">{project.full_name}</p>
                  <p className="text-zinc-400">
                    {project.language ?? "Unknown"} - {project.stars.toLocaleString()} stars
                  </p>
                  {project.description && (
                    <p className="mt-1 text-zinc-300">{project.description}</p>
                  )}
                  {project.html_url && (
                    <a
                      href={project.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-cyan-300 hover:underline"
                    >
                      Open Repository
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
          {!isLoading && projects.length > 0 && (
            <p className="mt-4 text-xs text-zinc-500">
              Showing {projects.length} result(s){query ? ` for "${query}"` : ""}.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
