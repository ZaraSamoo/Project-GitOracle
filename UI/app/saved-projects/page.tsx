import { ProjectPageTemplate } from "@/components/project-page-template";
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

export default async function SavedProjectsPage() {
  let repositories: RepositoryResponse["saved_projects"] = [];
  let repositoriesError: string | undefined;

  try {
    const data = await flaskRequest<RepositoryResponse>({ path: "/api/saved-projects" });
    repositories = data.saved_projects.slice(0, 6);
  } catch (error) {
    repositories = [];
    repositoriesError =
      error instanceof Error ? error.message : "Failed to fetch saved projects from Flask.";
  }

  return (
    <ProjectPageTemplate
      title="Saved Projects"
      subtitle="Keep your shortlisted repositories in one place and compare time estimates so you can decide what to build next."
      imageUrl="https://images.unsplash.com/photo-1484417894907-623942c8ee29?auto=format&fit=crop&w=1600&q=80"
      repositories={repositories}
      repositoriesError={repositoriesError}
    />
  );
}
