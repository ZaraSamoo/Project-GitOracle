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
            Discover high-signal repositories from your InternHub database, ready to explore.
          </p>
          {isLoading && <p className="mt-4 text-sm text-cyan-300">Loading results...</p>}
          {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
          {!error && !isLoading && projects.length === 0 && (
            <p className="mt-4 text-sm text-zinc-400">
              Enter a query and press Enter to search your database.
            </p>
          )}
          {!isLoading && projects.length > 0 && (
            <ul className="mt-4 space-y-4 text-sm">
              {projects.map((project) => (
                <li
                  key={project.repo_id}
                  className="rounded-xl border border-slate-700 bg-slate-800 p-4 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_10px_25px_rgba(0,0,0,0.3)]"
                >
                  {project.html_url ? (
                    <a
                      href={project.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lg font-semibold text-sky-400 no-underline hover:underline"
                    >
                      {project.full_name}
                    </a>
                  ) : (
                    <div className="text-lg font-semibold text-sky-400">
                      {project.full_name}
                    </div>
                  )}
                  <div className="mt-1 text-sm text-slate-400">
                    {project.language || "Unknown"} - ⭐{" "}
                    {project.stars?.toLocaleString?.() ?? 0}
                  </div>
                  <p className="mt-2 text-slate-300">
                    {(project.description || "No description available.").slice(0, 150)}
                    {(project.description || "").length > 150 ? "..." : ""}
                  </p>
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
