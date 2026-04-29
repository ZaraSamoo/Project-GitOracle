from __future__ import annotations

import glob
import logging
import os
import re
import time
from typing import Optional

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# ──────────────────────────────────────────────────────────────
# BOOTSTRAP
# ──────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# PATHS  — derived from this file's location inside DB\
#
# __file__  = DBMS_database\DB\ingest.py
# BASE_DIR  = DBMS_database\DB
# ROOT_DIR  = DBMS_database
# KAGGLE_DIR= DBMS_database\repos_folder
# ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))   # …\DB
ROOT_DIR   = os.path.dirname(BASE_DIR)                    # …\DBMS_database
KAGGLE_DIR = os.path.join(ROOT_DIR, "repos_folder")       # …\repos_folder

# ──────────────────────────────────────────────────────────────
# CONFIG  — override via .env file placed next to this script
# ──────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DB",       "github_recommender"),
    "user":     os.getenv("PG_USER",     "app_user"),
    "password": os.getenv("PG_PASSWORD", "password"),
}

GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
BATCH_SIZE      = int(os.getenv("BATCH_SIZE", "500"))
API_PER_PAGE    = 100
FUZZY_THRESHOLD = 0.4   # pg_trgm similarity() minimum for fuzzy match


# ══════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ══════════════════════════════════════════════════════════════

def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)


# ══════════════════════════════════════════════════════════════
# GITHUB API HELPERS
# ══════════════════════════════════════════════════════════════

def _github_headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _github_get(url: str, params: dict | None = None) -> Optional[dict | list]:
    """Single GitHub GET with rate-limit retry."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=_github_headers(),
                                params=params, timeout=15)
            if resp.status_code == 404:
                log.warning("404 Not Found: %s", url)
                return None
            if resp.status_code in (403, 429):
                reset = int(resp.headers.get("X-RateLimit-Reset",
                                              time.time() + 60))
                wait = max(reset - int(time.time()), 10)
                log.warning("Rate limited — sleeping %ds (attempt %d/3)", wait, attempt + 1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            log.error("Request error %s: %s", url, exc)
            time.sleep(5)
    return None


# ──────────────────────────────────────────────────────────────
# PHASE 3 — Fetch repos by GitHub USERNAME
# ──────────────────────────────────────────────────────────────
def fetch_repos_by_username(username: str) -> list[dict]:
    """
    GET /users/{username}/repos?type=all&per_page=100&page=N
    Returns a flat list of GitHub repo dicts.
    """
    all_repos: list[dict] = []
    page = 1
    log.info("Fetching repos for GitHub user: %s", username)

    while True:
        data = _github_get(
            f"https://api.github.com/users/{username}/repos",
            params={"type": "all", "per_page": API_PER_PAGE, "page": page},
        )
        if not data:
            break
        all_repos.extend(data)
        if len(data) < API_PER_PAGE:
            break
        page += 1
        time.sleep(0.5)

    log.info("Fetched %d repos for user '%s'", len(all_repos), username)
    return all_repos


def fetch_single_repo(full_name: str) -> Optional[dict]:
    """GET /repos/{owner}/{repo}  — used for individual lookups."""
    return _github_get(f"https://api.github.com/repos/{full_name}")


def fetch_issues(full_name: str, state: str = "open") -> list[dict]:
    """
    GET /repos/{owner}/{repo}/issues?state=open&per_page=100
    Paginates fully. Skips pull-requests automatically.
    """
    issues: list[dict] = []
    page = 1

    while True:
        data = _github_get(
            f"https://api.github.com/repos/{full_name}/issues",
            params={"state": state, "per_page": API_PER_PAGE, "page": page},
        )
        if not data:
            break
        # GitHub issues endpoint returns PRs too — filter them out
        issues.extend(i for i in data if "pull_request" not in i)
        if len(data) < API_PER_PAGE:
            break
        page += 1
        time.sleep(0.3)

    log.info("Fetched %d issues for %s", len(issues), full_name)
    return issues


# ══════════════════════════════════════════════════════════════
# PHASE 2 — KAGGLE DATA INGESTION
# ══════════════════════════════════════════════════════════════

def _detect_kaggle_file(directory: str) -> str:
    """
    Auto-detects the Kaggle dataset file inside `directory`.
    Preference order: repos.json > *.json.gz > *.json > *.csv.gz > *.csv

    For this project the file should be:
      DBMS_database\repos_folder\repos.json
    """
    # Explicit filename check first (your specific file)
    explicit = os.path.join(directory, "repos.json")
    if os.path.exists(explicit):
        log.info("Found Kaggle file: %s", explicit)
        return explicit

    patterns = ["*.json.gz", "*.jsonl.gz", "*.json", "*.csv.gz", "*.csv"]
    for pattern in patterns:
        found = glob.glob(os.path.join(directory, pattern))
        if found:
            log.info("Auto-detected Kaggle file: %s", found[0])
            return found[0]

    raise FileNotFoundError(
        f"No dataset file found in '{directory}'.\n"
        f"Expected: {explicit}\n"
        "Place your Kaggle download there (rename to repos.json if needed)."
    )


def load_kaggle_dataset(directory: str) -> pd.DataFrame:
    """
    Load Kaggle dataset from directory, auto-detecting file type.

    The pelmers dataset (repos.json) is a JSON array — NOT JSON-lines.
    pd.read_json without lines=True handles a JSON array correctly.
    If it IS lines format (one object per line), set lines=True below.
    """
    path = _detect_kaggle_file(directory)
    log.info("Loading: %s", path)

    if path.endswith((".json.gz", ".jsonl.gz")):
        # Compressed JSON-lines
        df = pd.read_json(path, lines=True, compression="infer")
    elif path.endswith(".json"):
        # Try JSON array first; fall back to JSON-lines on error
        try:
            df = pd.read_json(path)           # JSON array  [{ ... }, ...]
            if df.ndim == 1:
                # read_json returned a Series — it's actually JSON-lines
                df = pd.read_json(path, lines=True)
        except ValueError:
            df = pd.read_json(path, lines=True)
    else:
        df = pd.read_csv(path, compression="infer", low_memory=False)

    log.info("Raw rows: %d  |  Columns: %s", len(df), list(df.columns))
    return df


def _extract_str(val) -> Optional[str]:
    """Safely extract string from plain value or dict like {'name': 'Python'}."""
    if isinstance(val, dict):
        return val.get("name") or val.get("value") or None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return str(val).strip() or None


def _extract_topics(val) -> list[str]:
    """
    Handle all Kaggle topic formats:
      - {"nodes": [{"topic": {"name": "python"}}]}
      - ["python", "web"]
      - "python,web"
    """
    if isinstance(val, dict):
        nodes = val.get("nodes", [])
        return [n["topic"]["name"] for n in nodes
                if isinstance(n, dict) and "topic" in n]
    if isinstance(val, list):
        return [str(t).strip() for t in val if t]
    if isinstance(val, str) and val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return []


def clean_kaggle_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise Kaggle dataset columns to match schema.sql exactly.
    Handles camelCase field names from the pelmers dataset.
    """
    # ── Rename camelCase -> snake_case ─────────────────────
    col_map = {
        "nameWithOwner":    "full_name",
        "stargazerCount":   "stars",
        "forkCount":        "forks",
        "primaryLanguage":  "language",
        "createdAt":        "created_at",
        "updatedAt":        "updated_at",
        "description":      "description",
        "isFork":           "is_fork",
        "openIssueCount":   "open_issues",
        "watchers":         "watchers",
        "licenseInfo":      "license_name",
        "repositoryTopics": "topics",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # ── Require full_name ───────────────────────────────────
    if "full_name" not in df.columns:
        raise ValueError("Dataset has no 'nameWithOwner' or 'full_name' column.")
    df = df.dropna(subset=["full_name"])
    df = df[df["full_name"].str.contains("/", na=False)]

    # ── Derive owner + name ─────────────────────────────────
    split = df["full_name"].str.split("/", n=1, expand=True)
    df["owner"] = split[0].str.strip()   # -> repositories.owner
    df["name"]  = split[1].str.strip()   # -> repositories.name

    # ── Numeric ─────────────────────────────────────────────
    for col in ["stars", "forks"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)
        else:
            df[col] = 0

    # ── Language / license (may be dicts) ──────────────────
    for col in ["language", "license_name"]:
        if col in df.columns:
            df[col] = df[col].apply(_extract_str)

    # ── Topics ──────────────────────────────────────────────
    if "topics" in df.columns:
        df["topics"] = df["topics"].apply(_extract_topics)
    else:
        df["topics"] = [[] for _ in range(len(df))]

    # ── html_url — construct if absent ──────────────────────
    if "html_url" not in df.columns:
        df["html_url"] = "https://github.com/" + df["full_name"]

    # ── Timestamps ──────────────────────────────────────────
    for col in ["created_at", "updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    # ── Deduplicate on full_name (keep highest stars) ───────
    before = len(df)
    df = df.sort_values("stars", ascending=False).drop_duplicates(
        subset=["full_name"], keep="first"
    )
    log.info("Deduplication removed %d rows. Remaining: %d", before - len(df), len(df))

    # ── Drop rows with empty owner or name ──────────────────
    df = df[df["owner"].str.len() > 0]
    df = df[df["name"].str.len() > 0]

    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# TOPIC HELPERS
# ══════════════════════════════════════════════════════════════

def upsert_topics(conn, repo_id: int, topics: list[str]) -> None:
    """
    Insert topic names into repo_topics (ON CONFLICT DO NOTHING),
    then link them to the repository in repository_topics.
    """
    if not topics:
        return

    with conn.cursor() as cur:
        for topic in topics:
            topic = topic.strip().lower()
            if not topic:
                continue
            cur.execute(
                "INSERT INTO repo_topics(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (topic,),
            )
            cur.execute("SELECT topic_id FROM repo_topics WHERE name = %s", (topic,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    INSERT INTO repository_topics(repo_id, topic_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (repo_id, row[0]),
                )


# ══════════════════════════════════════════════════════════════
# PHASE 2 — INSERT KAGGLE DATA INTO repositories
# ══════════════════════════════════════════════════════════════

# Kaggle rows have no github_id — derive a stable surrogate via hashtext().
_KAGGLE_UPSERT = """
INSERT INTO repositories
    (github_id, owner, name, full_name, description,
     stars, forks, language, html_url)
VALUES
    (
        abs(hashtext(%(full_name)s)),
        %(owner)s,
        %(name)s,
        %(full_name)s,
        %(description)s,
        %(stars)s,
        %(forks)s,
        %(language)s,
        %(html_url)s
    )
ON CONFLICT (full_name) DO UPDATE SET
    stars       = GREATEST(EXCLUDED.stars,       repositories.stars),
    forks       = GREATEST(EXCLUDED.forks,       repositories.forks),
    language    = COALESCE(EXCLUDED.language,    repositories.language),
    description = COALESCE(EXCLUDED.description, repositories.description),
    html_url    = COALESCE(EXCLUDED.html_url,    repositories.html_url)
RETURNING repo_id
"""

# GitHub API rows have a real github_id
_REPO_UPSERT = """
INSERT INTO repositories
    (github_id, owner, name, full_name, description,
     stars, forks, language, html_url, created_at)
VALUES
    (%(github_id)s, %(owner)s, %(name)s, %(full_name)s, %(description)s,
     %(stars)s, %(forks)s, %(language)s, %(html_url)s, %(created_at)s)
ON CONFLICT (full_name) DO UPDATE SET
    github_id   = EXCLUDED.github_id,
    stars       = GREATEST(EXCLUDED.stars,       repositories.stars),
    forks       = GREATEST(EXCLUDED.forks,       repositories.forks),
    language    = COALESCE(EXCLUDED.language,    repositories.language),
    description = COALESCE(EXCLUDED.description, repositories.description),
    html_url    = COALESCE(EXCLUDED.html_url,    repositories.html_url)
RETURNING repo_id
"""


def insert_kaggle_repos(df: pd.DataFrame, conn) -> None:
    """
    Batch-upsert cleaned Kaggle DataFrame into repositories.
    Topics are inserted and linked after each repo row.
    """
    total = len(df)
    log.info("Upserting %d Kaggle repos …", total)

    with conn.cursor() as cur:
        for start in tqdm(range(0, total, BATCH_SIZE), desc="Kaggle->DB"):
            batch = df.iloc[start: start + BATCH_SIZE]
            for _, row in batch.iterrows():
                params = {
                    "full_name":   row["full_name"],
                    "owner":       row["owner"],
                    "name":        row["name"],
                    "description": (str(row.get("description") or "")[:2000]) or None,
                    "stars":       int(row["stars"]),
                    "forks":       int(row["forks"]),
                    "language":    row.get("language"),
                    "html_url":    row.get("html_url"),
                }
                cur.execute(_KAGGLE_UPSERT, params)
                result = cur.fetchone()
                if result:
                    upsert_topics(conn, result[0], row.get("topics") or [])
            conn.commit()

    log.info("Kaggle upsert complete.")


# ══════════════════════════════════════════════════════════════
# PHASE 3 — INSERT GITHUB API DATA (fetched by username)
# ══════════════════════════════════════════════════════════════

def insert_github_repos(api_repos: list[dict], conn) -> dict[str, int]:
    """
    Upsert repos fetched from GitHub API.
    Returns mapping {full_name: repo_id} for the linking step.
    """
    mapping: dict[str, int] = {}

    with conn.cursor() as cur:
        for repo in tqdm(api_repos, desc="GitHub->DB"):
            params = {
                "github_id":   repo["id"],
                "owner":       repo["owner"]["login"],
                "name":        repo["name"],
                "full_name":   repo["full_name"],
                "description": (repo.get("description") or "")[:2000] or None,
                "stars":       repo.get("stargazers_count", 0),
                "forks":       repo.get("forks_count", 0),
                "language":    (repo.get("language") or "").lower() or None,
                "html_url":    repo.get("html_url"),
                "created_at":  repo.get("created_at"),
            }
            cur.execute(_REPO_UPSERT, params)
            result = cur.fetchone()
            if result:
                repo_id = result[0]
                mapping[repo["full_name"]] = repo_id
                upsert_topics(conn, repo_id, repo.get("topics") or [])
        conn.commit()

    log.info("GitHub upsert: %d repos stored.", len(mapping))
    return mapping


# ══════════════════════════════════════════════════════════════
# PHASE 4 — KAGGLE <-> GITHUB LINKING
# ══════════════════════════════════════════════════════════════

def link_kaggle_to_github(conn) -> dict:
    """
    Three-tier matching strategy run entirely in SQL.

    Tier 1 — Exact full_name: handled automatically by ON CONFLICT at insert time.
    Tier 2 — Name match: LOWER(kaggle.name) = LOWER(github.name)
    Tier 3 — Fuzzy: similarity(kaggle.name, github.name) > FUZZY_THRESHOLD
    """
    stats = {"tier2": 0, "tier3": 0, "unmatched": 0}

    with conn.cursor() as cur:

        # ── TIER 2: name-only match ───────────────────────────
        cur.execute("""
            UPDATE repositories AS kaggle
            SET
                github_id   = github.github_id,
                stars       = GREATEST(kaggle.stars,  github.stars),
                forks       = GREATEST(kaggle.forks,  github.forks),
                language    = COALESCE(github.language,    kaggle.language),
                description = COALESCE(github.description, kaggle.description),
                html_url    = COALESCE(github.html_url,    kaggle.html_url)
            FROM repositories AS github
            WHERE
                kaggle.github_id = abs(hashtext(kaggle.full_name))
                AND github.github_id <> abs(hashtext(github.full_name))
                AND LOWER(kaggle.name) = LOWER(github.name)
                AND kaggle.full_name   <> github.full_name
            RETURNING kaggle.repo_id
        """)
        stats["tier2"] = cur.rowcount
        conn.commit()

        # ── TIER 3: fuzzy similarity ──────────────────────────
        cur.execute(f"""
            UPDATE repositories AS kaggle
            SET
                github_id   = github.github_id,
                stars       = GREATEST(kaggle.stars,  github.stars),
                forks       = GREATEST(kaggle.forks,  github.forks),
                language    = COALESCE(github.language,    kaggle.language),
                description = COALESCE(github.description, kaggle.description),
                html_url    = COALESCE(github.html_url,    kaggle.html_url)
            FROM (
                SELECT DISTINCT ON (k.repo_id)
                    k.repo_id AS kaggle_repo_id,
                    g.github_id,
                    g.stars, g.forks, g.language, g.description, g.html_url
                FROM repositories k
                JOIN repositories g ON
                    k.github_id = abs(hashtext(k.full_name))
                    AND g.github_id <> abs(hashtext(g.full_name))
                    AND k.full_name <> g.full_name
                    AND LOWER(k.name) <> LOWER(g.name)
                    AND similarity(k.name, g.name) > {FUZZY_THRESHOLD}
                ORDER BY k.repo_id, similarity(k.name, g.name) DESC
            ) AS github
            WHERE kaggle.repo_id = github.kaggle_repo_id
            RETURNING kaggle.repo_id
        """)
        stats["tier3"] = cur.rowcount
        conn.commit()

        # ── Count still-unmatched ─────────────────────────────
        cur.execute("""
            SELECT COUNT(*) FROM repositories
            WHERE github_id = abs(hashtext(full_name))
        """)
        stats["unmatched"] = cur.fetchone()[0]

    log.info(
        "Linking complete -> Tier2 (name): %d | Tier3 (fuzzy): %d | Unmatched: %d",
        stats["tier2"], stats["tier3"], stats["unmatched"],
    )
    return stats


# ══════════════════════════════════════════════════════════════
# PHASE 5 — ISSUE INGESTION
# ══════════════════════════════════════════════════════════════

_ISSUE_UPSERT = """
INSERT INTO issues
    (github_issue_id, repo_id, title, body, state,
     github_url, created_at, updated_at)
VALUES
    (%(github_issue_id)s, %(repo_id)s, %(title)s, %(body)s, %(state)s,
     %(github_url)s, %(created_at)s, %(updated_at)s)
ON CONFLICT (github_issue_id) DO UPDATE SET
    title      = EXCLUDED.title,
    body       = EXCLUDED.body,
    state      = EXCLUDED.state,
    github_url = EXCLUDED.github_url,
    updated_at = EXCLUDED.updated_at
RETURNING issue_id
"""


def insert_issues(full_name: str, conn) -> int:
    """
    Fetch all open issues for `full_name` from GitHub API and upsert.
    Also inserts issue_labels rows.
    Returns count of issues inserted/updated.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT repo_id FROM repositories WHERE full_name = %s",
            (full_name,),
        )
        row = cur.fetchone()
    if not row:
        log.error("Repo '%s' not in DB. Run ingestion first.", full_name)
        return 0

    repo_id = row[0]
    issues  = fetch_issues(full_name, state="open")
    count   = 0

    with conn.cursor() as cur:
        for iss in issues:
            params = {
                "github_issue_id": iss["id"],
                "repo_id":         repo_id,
                "title":           iss["title"][:500],
                "body":            (iss.get("body") or "")[:10000] or None,
                "state":           iss.get("state", "open"),
                "github_url":      iss.get("html_url"),
                "created_at":      iss.get("created_at"),
                "updated_at":      iss.get("updated_at"),
            }
            cur.execute(_ISSUE_UPSERT, params)
            result = cur.fetchone()
            if result:
                issue_id = result[0]
                count += 1
                for label in iss.get("labels", []):
                    cur.execute(
                        """
                        INSERT INTO issue_labels(issue_id, name, color)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (issue_id, name) DO NOTHING
                        """,
                        (issue_id, label["name"], label.get("color")),
                    )
        conn.commit()

    log.info("Inserted %d issues for '%s'", count, full_name)
    return count


# ══════════════════════════════════════════════════════════════
# VALIDATION QUERIES
# ══════════════════════════════════════════════════════════════

VALIDATION_QUERIES = {
    "linked_repos": """
        SELECT full_name, owner, name, stars, language, html_url
        FROM   repositories
        WHERE  github_id <> abs(hashtext(full_name))
        ORDER  BY stars DESC
        LIMIT  20;
    """,
    "unmatched_kaggle": """
        SELECT full_name, owner, name, stars
        FROM   repositories
        WHERE  github_id = abs(hashtext(full_name))
        ORDER  BY stars DESC
        LIMIT  20;
    """,
    "top_by_stars": """
        SELECT full_name, stars, forks, language, html_url
        FROM   repositories
        ORDER  BY stars DESC
        LIMIT  10;
    """,
    "repos_with_issues": """
        SELECT r.full_name, r.stars, r.language,
               COUNT(i.issue_id) AS open_issues
        FROM   repositories r
        LEFT JOIN issues i ON i.repo_id = r.repo_id AND i.state = 'open'
        GROUP  BY r.repo_id
        ORDER  BY open_issues DESC
        LIMIT  20;
    """,
}


def run_validation(conn) -> None:
    """Print results of all validation queries."""
    with conn.cursor() as cur:
        for name, sql in VALIDATION_QUERIES.items():
            log.info("── Validation: %s ──", name)
            cur.execute(sql)
            rows = cur.fetchall()
            col_names = [d[0] for d in cur.description]
            log.info("  Columns: %s", col_names)
            for row in rows[:5]:
                log.info("  %s", row)
            log.info("  (total %d rows)", len(rows))


# ══════════════════════════════════════════════════════════════
# HIGH-LEVEL PIPELINES
# ══════════════════════════════════════════════════════════════

def run_kaggle_pipeline(kaggle_dir: str = KAGGLE_DIR) -> None:
    """
    Full Kaggle ingestion:
      1. Detect + load dataset file from kaggle_dir
      2. Clean and normalise
      3. Upsert into repositories + repo_topics + repository_topics
    """
    df = load_kaggle_dataset(kaggle_dir)
    df = clean_kaggle_dataset(df)

    conn = get_connection()
    try:
        insert_kaggle_repos(df, conn)
        log.info("Kaggle pipeline done. %d repos upserted.", len(df))
    finally:
        conn.close()


def run_github_username_pipeline(username: str, fetch_issues_flag: bool = False) -> None:
    """
    GitHub username pipeline:
      1. Fetch all repos for username from API
      2. Upsert into repositories (using real github_id)
      3. Run Kaggle <-> GitHub linking
      4. (Optional) fetch issues for each repo
    """
    api_repos = fetch_repos_by_username(username)
    if not api_repos:
        log.warning("No repos returned for user '%s'", username)
        return

    conn = get_connection()
    try:
        insert_github_repos(api_repos, conn)
        link_kaggle_to_github(conn)

        if fetch_issues_flag:
            for repo in api_repos:
                insert_issues(repo["full_name"], conn)
                time.sleep(0.5)

        log.info("GitHub pipeline done for user '%s'.", username)
    finally:
        conn.close()


def run_full_pipeline(
    kaggle_dir: str = KAGGLE_DIR,
    github_username: str | None = None,
    fetch_issues_flag: bool = False,
) -> None:
    """
    End-to-end pipeline:
      Phase 2 -> Phase 3 -> Phase 4 (linking) -> Phase 5 (issues)
    """
    run_kaggle_pipeline(kaggle_dir)

    if github_username:
        run_github_username_pipeline(github_username, fetch_issues_flag)

    conn = get_connection()
    try:
        run_validation(conn)
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    """
    Usage examples (run from DBMS_database\DB\):

      # Load Kaggle data only (reads DBMS_database\repos_folder\repos.json)
      python ingest.py kaggle

      # Load GitHub repos for a username (with issue fetch)
      python ingest.py github torvalds --issues

      # Full pipeline: Kaggle + GitHub username
      python ingest.py full octocat --issues

      # Validate only
      python ingest.py validate
    """

    cmd = sys.argv[1] if len(sys.argv) > 1 else "full"

    if cmd == "kaggle":
        run_kaggle_pipeline()

    elif cmd == "github":
        if len(sys.argv) < 3:
            print("Usage: python ingest.py github <github_username> [--issues]")
            sys.exit(1)
        uname             = sys.argv[2]
        fetch_issues_flag = "--issues" in sys.argv
        run_github_username_pipeline(uname, fetch_issues_flag)

    elif cmd == "full":
        uname             = sys.argv[2] if len(sys.argv) > 2 else None
        fetch_issues_flag = "--issues" in sys.argv
        run_full_pipeline(
            kaggle_dir=KAGGLE_DIR,
            github_username=uname,
            fetch_issues_flag=fetch_issues_flag,
        )

    elif cmd == "validate":
        conn = get_connection()
        try:
            run_validation(conn)
        finally:
            conn.close()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
