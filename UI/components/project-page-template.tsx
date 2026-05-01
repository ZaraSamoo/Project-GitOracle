import { AppHeader } from "@/components/app-header";

interface ProjectPageTemplateProps {
  title: string;
  subtitle: string;
  imageUrl: string;
  repositories?: Array<{
    repo_id: number;
    full_name: string;
    description: string | null;
    owner: string;
    language: string | null;
    stars: number;
    forks: number;
    html_url: string | null;
  }>;
  repositoriesError?: string;
  loading?: boolean;
  emptyMessage?: string;
}

export function ProjectPageTemplate({
  title,
  subtitle,
  imageUrl,
  repositories = [],
  repositoriesError,
  loading = false,
  emptyMessage = "No repositories available from `/api/saved-repos`.",
}: ProjectPageTemplateProps) {
  return (
    <div className="min-h-screen bg-black text-white">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl md:text-5xl font-bold">{title}</h1>
        <p className="mt-3 max-w-3xl text-zinc-300">{subtitle}</p>
        <div className="mt-8 overflow-hidden rounded-2xl border border-white/10">
          <img src={imageUrl} alt={title} className="h-[360px] w-full object-cover" />
        </div>
        <section className="mt-8 rounded-2xl border border-white/10 bg-zinc-950/60 p-5">
          <h2 className="text-xl font-semibold">Saved Repositories from Flask</h2>
          {loading ? (
            <p className="mt-3 text-sm text-zinc-300">Loading your saved repositories...</p>
          ) : repositoriesError ? (
            <p className="mt-3 text-sm text-rose-300">{repositoriesError}</p>
          ) : repositories.length === 0 ? (
            <p className="mt-3 text-sm text-zinc-400">{emptyMessage}</p>
          ) : (
            <ul className="mt-4 space-y-4 text-sm">
              {repositories.map((repo) => (
                <li
                  key={repo.repo_id}
                  className="rounded-xl border border-slate-700 bg-slate-800 p-4 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_10px_25px_rgba(0,0,0,0.3)]"
                >
                  {repo.html_url ? (
                    <a
                      href={repo.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lg font-semibold text-sky-400 no-underline hover:underline"
                    >
                      {repo.full_name}
                    </a>
                  ) : (
                    <div className="text-lg font-semibold text-sky-400">{repo.full_name}</div>
                  )}
                  <div className="mt-1 text-sm text-slate-400">
                    {repo.language || "Unknown"} - ⭐ {repo.stars?.toLocaleString?.() ?? 0}
                  </div>
                  <p className="mt-2 text-slate-300">
                    {(repo.description || "No description available.").slice(0, 150)}
                    {(repo.description || "").length > 150 ? "..." : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
