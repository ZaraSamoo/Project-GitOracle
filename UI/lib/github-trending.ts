const GITHUB_TRENDING_URL = "https://github.com/trending";
const API_BASE = "https://api.github.com/repos";
const MAX_REPOS = 5;

const REQUEST_HEADERS = {
  "User-Agent": "Mozilla/5.0 GitOracle",
  Accept: "application/vnd.github+json",
};

export type RepoDifficulty = "low" | "medium" | "amateur" | "high";

export interface TrendingRepo {
  id: string;
  name: string;
  owner: string;
  url: string;
  stars: number;
  forks: number;
  openIssues: number;
  watchers: number;
  sizeKb: number;
  contributors: number;
  pullRequests: number;
  commitActivity: "Low" | "Medium" | "High" | "N/A";
  languages: string[];
  difficulty: RepoDifficulty;
}

const cleanNumber = (value: string) => Number.parseInt(value.replace(/[^\d]/g, ""), 10) || 0;

const getDifficultyTag = (repo: Omit<TrendingRepo, "difficulty">): RepoDifficulty => {
  if (repo.openIssues > 150 || repo.pullRequests > 30 || repo.sizeKb > 900000) return "high";
  if (repo.contributors > 100 || repo.languages.length > 4 || repo.commitActivity === "High") return "amateur";
  if (repo.contributors > 25 || repo.openIssues > 40 || repo.commitActivity === "Medium") return "medium";
  return "low";
};

const parseTrendingRepos = (html: string) => {
  const articleRegex = /<article[\s\S]*?class="Box-row"[\s\S]*?<\/article>/g;
  const articles = html.match(articleRegex) ?? [];

  return articles.slice(0, MAX_REPOS).map((article) => {
    const hrefMatch = article.match(/href="\/([^"\/]+\/[^"\/]+)"/);
    const [owner = "", repo = ""] = (hrefMatch?.[1] ?? "").split("/");
    const starsAndForks = [...article.matchAll(/<a[^>]*class="[^"]*Link--muted[^"]*"[^>]*>\s*([\d,]+)\s*<\/a>/g)];

    return {
      owner,
      repo,
      name: `${owner}/${repo}`,
      url: `https://github.com/${owner}/${repo}`,
      stars: cleanNumber(starsAndForks[0]?.[1] ?? "0"),
      forks: cleanNumber(starsAndForks[1]?.[1] ?? "0"),
    };
  });
};

const fetchJson = async (url: string) => {
  const response = await fetch(url, { headers: REQUEST_HEADERS, next: { revalidate: 3600 } });
  if (!response.ok) return null;
  return response.json();
};

const enrichRepo = async (repo: ReturnType<typeof parseTrendingRepos>[number]) => {
  const [basic, contributors, pulls, commits, languages] = await Promise.all([
    fetchJson(`${API_BASE}/${repo.owner}/${repo.repo}`),
    fetchJson(`${API_BASE}/${repo.owner}/${repo.repo}/contributors?per_page=100`),
    fetchJson(`${API_BASE}/${repo.owner}/${repo.repo}/pulls?per_page=30`),
    fetchJson(`${API_BASE}/${repo.owner}/${repo.repo}/commits?per_page=30`),
    fetchJson(`${API_BASE}/${repo.owner}/${repo.repo}/languages`),
  ]);

  const commitCount = Array.isArray(commits) ? commits.length : 0;
  const commitActivity: TrendingRepo["commitActivity"] =
    commitCount < 2 ? "Low" : commitCount > 20 ? "High" : "Medium";

  const baseRepo = {
    id: repo.name,
    name: repo.name,
    owner: repo.owner,
    url: repo.url,
    stars: basic?.stargazers_count ?? repo.stars,
    forks: basic?.forks_count ?? repo.forks,
    openIssues: basic?.open_issues_count ?? 0,
    watchers: basic?.watchers_count ?? 0,
    sizeKb: basic?.size ?? 0,
    contributors: Array.isArray(contributors) ? contributors.length : 0,
    pullRequests: Array.isArray(pulls) ? pulls.length : 0,
    commitActivity,
    languages: languages ? Object.keys(languages) : [],
  };

  return {
    ...baseRepo,
    difficulty: getDifficultyTag(baseRepo),
  } satisfies TrendingRepo;
};

export const getTrendingRepos = async (): Promise<TrendingRepo[]> => {
  const htmlResponse = await fetch(GITHUB_TRENDING_URL, {
    headers: REQUEST_HEADERS,
    next: { revalidate: 3600 },
  });
  if (!htmlResponse.ok) return [];

  const html = await htmlResponse.text();
  const repos = parseTrendingRepos(html);
  if (!repos.length) return [];

  return Promise.all(repos.map((repo) => enrichRepo(repo)));
};
