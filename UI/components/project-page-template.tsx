import { AppHeader } from "@/components/app-header";

interface ProjectPageTemplateProps {
  title: string;
  subtitle: string;
  imageUrl: string;
  repositories?: Array<{
    repo_id: number;
    full_name: string;
    owner: string;
    language: string | null;
    stars: number;
    forks: number;
    html_url: string;
  }>;
  repositoriesError?: string;
}

export function ProjectPageTemplate({
  title,
  subtitle,
  imageUrl,
  repositories = [],
  repositoriesError,
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
          {repositoriesError ? (
            <p className="mt-3 text-sm text-rose-300">{repositoriesError}</p>
          ) : repositories.length === 0 ? (
            <p className="mt-3 text-sm text-zinc-400">No repositories available from `/api/saved-projects`.</p>
          ) : (
            <ul className="mt-4 space-y-2 text-sm">
              {repositories.map((repo) => (
                <li
                  key={repo.repo_id}
                  className="flex items-center justify-between rounded-lg border border-white/10 bg-black/30 px-4 py-3"
                >
                  <div>
                    <p className="font-medium">{repo.full_name}</p>
                    <p className="text-zinc-400">
                      {repo.language ?? "Unknown"} - {repo.stars.toLocaleString()} stars
                    </p>
                  </div>
                  <a
                    href={repo.html_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-cyan-300 hover:underline"
                  >
                    Open
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
