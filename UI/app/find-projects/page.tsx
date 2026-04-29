"use client";

import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { PromptInputBox } from "@/components/ui/ai-prompt-box";
import { flaskRequest } from "@/lib/flask-api";

interface RecommendationResponse {
  count: number;
  recommendations: Array<{
    user_id: number;
    issue_id: number;
    score: number;
    generated_at: string;
  }>;
}

interface IssuesResponse {
  count: number;
  issues: Array<{
    issue_id: number;
    title: string;
    repo_id: number;
    complexity: number | null;
    estimated_time: number | null;
  }>;
}

export default function FindProjectsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationResponse["recommendations"]>([]);
  const [fallbackIssues, setFallbackIssues] = useState<IssuesResponse["issues"]>([]);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    setError(null);
    setFallbackIssues([]);
    try {
      const data = await flaskRequest<RecommendationResponse>({ path: "/api/recommendations" });
      setRecommendations(data.recommendations);
    } catch {
      try {
        const issueData = await flaskRequest<IssuesResponse>({ path: "/api/issues" });
        setRecommendations([]);
        setFallbackIssues(issueData.issues);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to fetch data from Flask API."
        );
      }
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
              placeholder="Example: I have 6 hours this week and want a Python data project with clear milestones."
              isLoading={isLoading}
              onSend={async (message, files) => {
                console.log("Find Projects prompt:", message, files);
                await fetchRecommendations();
              }}
            />
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-white/10 bg-zinc-950/60 p-5 md:p-8">
          <h2 className="text-xl font-semibold">Flask Recommendations</h2>
          <p className="mt-2 text-sm text-zinc-400">
            This section now reads recommendation data from your Flask backend.
          </p>
          {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
          {!error && recommendations.length === 0 && (
            <p className="mt-4 text-sm text-zinc-400">
              Send a prompt to fetch recommendations from `/api/recommendations`.
            </p>
          )}
          {recommendations.length > 0 && (
            <ul className="mt-4 space-y-2 text-sm">
              {recommendations.map((rec) => (
                <li
                  key={`${rec.user_id}-${rec.issue_id}`}
                  className="rounded-xl border border-white/10 bg-black/30 px-4 py-3"
                >
                  User {rec.user_id} {"->"} Issue {rec.issue_id} (score {rec.score.toFixed(2)})
                </li>
              ))}
            </ul>
          )}
          {fallbackIssues.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-amber-300">
                `/api/recommendations` is currently unavailable. Showing open issues from
                `/api/issues` instead.
              </p>
              <ul className="mt-3 space-y-2 text-sm">
                {fallbackIssues.map((issue) => (
                  <li
                    key={issue.issue_id}
                    className="rounded-xl border border-white/10 bg-black/30 px-4 py-3"
                  >
                    #{issue.issue_id} {issue.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
