from __future__ import annotations

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

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# PATHS
# __file__  = DBMS_database\DB\Py_file.py
# BASE_DIR  = DBMS_database\DB
# ROOT_DIR  = DBMS_database
# KAGGLE_DIR= DBMS_database\repos_folder
# ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(BASE_DIR)
KAGGLE_DIR = os.path.join(ROOT_DIR, "repos_folder")
KAGGLE_JSON = os.path.join(KAGGLE_DIR, "repos.json")   # your specific file

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DB",       "github_recommender"),
    "user":     os.getenv("PG_USER",     "app_user"),
    "password": os.getenv("PG_PASSWORD", "password"),
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BATCH_SIZE   = int(os.getenv("BATCH_SIZE", "500"))
API_PER_PAGE = 100


# ──────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────
def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)


# ──────────────────────────────────────────────────────────────
# URL / NAME HELPERS
# ──────────────────────────────────────────────────────────────
def resolve_html_url(row: dict) -> str:
    """
    Construct the GitHub browser URL for a repo row.
    Priority: html_url field -> full_name -> owner+name fields.
    """
    html_url = (row.get("html_url") or "").strip()
    if html_url.startswith("https://github.com/"):
        return html_url

    full_name = (row.get("nameWithOwner") or row.get("full_name") or "").strip()
    if "/" in full_name:
        return f"https://github.com/{full_name}"

    owner = (row.get("owner") or "").strip()
    name  = (row.get("name")  or "").strip()
    if owner and name:
        return f"https://github.com/{owner}/{name}"

    raise ValueError(f"Cannot resolve html_url for: {row}")


def parse_owner_name(full_name: str) -> tuple[str, str]:
    """Split 'owner/repo' into (owner, repo)."""
    parts = full_name.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid full_name: '{full_name}'")
    return parts[0].strip(), parts[1].strip()


# ──────────────────────────────────────────────────────────────
# KAGGLE DATASET LOADING
# ──────────────────────────────────────────────────────────────
def load_kaggle_dataset(path: str) -> pd.DataFrame:
    """
    Load the pelmers/github-repository-metadata-with-5-stars dataset.
    Supports: .json (array or lines), .json.gz, .jsonl.gz, .csv, .csv.gz
    """
    log.info("Loading Kaggle dataset from: %s", path)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Place repos.json inside DBMS_database\\repos_folder\\"
        )

    if path.endswith((".json.gz", ".jsonl.gz")):
        df = pd.read_json(path, lines=True, compression="infer")
    elif path.endswith(".json"):
        try:
            df = pd.read_json(path)
            if df.ndim == 1:
                df = pd.read_json(path, lines=True)
        except ValueError:
            df = pd.read_json(path, lines=True)
    else:
        df = pd.read_csv(path, compression="infer", low_memory=False)

    log.info("Loaded %d raw rows, columns: %s", len(df), list(df.columns))
    return df


def _extract_str_field(val) -> Optional[str]:
    """Extract string from a plain value or a dict like {'name': 'Python'}."""
    if isinstance(val, dict):
        return val.get("name") or val.get("value") or None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return s or None


def _extract_topics(val) -> list[str]:
    """Normalise all Kaggle topic formats to a plain list of strings."""
    if isinstance(val, dict):
        nodes = val.get("nodes", [])
        return [n["topic"]["name"] for n in nodes if isinstance(n, dict) and "topic" in n]
    if isinstance(val, list):
        return [str(t).strip() for t in val if t]
    if isinstance(val, str) and val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return []


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise Kaggle dataset columns to match schema.sql.
    Returns a DataFrame with columns matching the repositories table.
    """
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

    if "full_name" not in df.columns:
        raise ValueError("Dataset missing 'nameWithOwner' or 'full_name' column.")

    df = df.dropna(subset=["full_name"])
    df = df[df["full_name"].str.contains("/", na=False)]

    split       = df["full_name"].str.split("/", n=1, expand=True)
    df["owner"] = split[0].str.strip()   # -> repositories.owner
    df["name"]  = split[1].str.strip()   # -> repositories.name

    for col in ["stars", "forks"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0).clip(lower=0).astype(int)

    for col in ["language", "license_name"]:
        if col in df.columns:
            df[col] = df[col].apply(_extract_str_field)

    if "topics" in df.columns:
        df["topics"] = df["topics"].apply(_extract_topics)
    else:
        df["topics"] = [[] for _ in range(len(df))]

    if "html_url" not in df.columns:
        df["html_url"] = "https://github.com/" + df["full_name"]

    for col in ["created_at", "updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    return df.reset_index(drop=True)


def validate_and_fix(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate, validate URLs, clamp numeric columns."""
    df = df.sort_values("stars", ascending=False)
    before = len(df)
    df = df.drop_duplicates(subset=["full_name"], keep="first")
    log.info("Deduplication: removed %d rows", before - len(df))

    df["language"] = df["language"].where(df["language"].notna(), other=None)
    df = df[df["owner"].str.len() > 0]
    df = df[df["name"].str.len() > 0]

    url_re   = re.compile(r"^https://github\.com/[^/]+/[^/]+")
    bad_urls = ~df["html_url"].str.match(url_re)
    if bad_urls.any():
        log.warning("Removing %d rows with malformed html_url", bad_urls.sum())
        df = df[~bad_urls]

    df["stars"] = df["stars"].clip(lower=0)
    df["forks"] = df["forks"].clip(lower=0)

    return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# TOPIC HELPERS
# ──────────────────────────────────────────────────────────────
def upsert_topics(conn, repo_id: int, topics: list[str]) -> None:
    """Insert topics and link them to a repository."""
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


# ──────────────────────────────────────────────────────────────
# BULK INSERT — KAGGLE REPOS
# ──────────────────────────────────────────────────────────────
def insert_repositories(df: pd.DataFrame, conn) -> None:
    """
    Batch-upsert repositories from cleaned Kaggle DataFrame.
    Uses execute_values for performance.
    Columns match schema.sql repositories table exactly.
    """
    total = len(df)
    log.info("Upserting %d repositories in batches of %d …", total, BATCH_SIZE)

    with conn.cursor() as cur:
        for start in tqdm(range(0, total, BATCH_SIZE), desc="Repos"):
            batch = df.iloc[start: start + BATCH_SIZE]

            values = []
            topics_map: dict[int, list[str]] = {}   # index -> topics list
            for idx, (_, r) in enumerate(batch.iterrows()):
                values.append((
                    abs(hash(r["full_name"])) % (2**31),  # surrogate github_id
                    r["owner"],
                    r["name"],
                    r["full_name"],
                    (r.get("description") or "")[:2000] or None,
                    int(r["stars"]),
                    int(r["forks"]),
                    r.get("language"),
                    r.get("html_url"),
                ))
                topics_map[idx] = r.get("topics") or []

            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO repositories
                    (github_id, owner, name, full_name, description,
                     stars, forks, language, html_url)
                VALUES %s
                ON CONFLICT (full_name) DO UPDATE SET
                    stars       = GREATEST(EXCLUDED.stars,       repositories.stars),
                    forks       = GREATEST(EXCLUDED.forks,       repositories.forks),
                    language    = COALESCE(EXCLUDED.language,    repositories.language),
                    description = COALESCE(EXCLUDED.description, repositories.description),
                    html_url    = COALESCE(EXCLUDED.html_url,    repositories.html_url)
                RETURNING repo_id, full_name
                """,
                values,
                page_size=BATCH_SIZE,
                fetch=True,
            )
            # execute_values with fetch=True returns rows from RETURNING
            returned_rows = cur.fetchall()  # [(repo_id, full_name), ...]

            # Build full_name -> repo_id map for topic linking
            fn_to_id = {fn: rid for rid, fn in returned_rows}

            # Re-iterate batch in order to link topics
            for idx, (_, r) in enumerate(batch.iterrows()):
                repo_id = fn_to_id.get(r["full_name"])
                if repo_id and topics_map[idx]:
                    upsert_topics(conn, repo_id, topics_map[idx])

            conn.commit()

    log.info("Repository upsert complete.")


# ──────────────────────────────────────────────────────────────
# GITHUB API HELPERS
# ──────────────────────────────────────────────────────────────
def _github_headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def fetch_repo_from_api(full_name: str) -> Optional[dict]:
    """GET /repos/{owner}/{repo}"""
    url = f"https://api.github.com/repos/{full_name}"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 404:
            log.warning("Repo not found: %s", full_name)
            return None
        if resp.status_code in (403, 429):
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait  = max(reset - int(time.time()), 5)
            log.warning("Rate limited. Sleeping %ds …", wait)
            time.sleep(wait)
            return fetch_repo_from_api(full_name)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error("API error for %s: %s", full_name, e)
        return None


def fetch_issues_from_api(full_name: str, state: str = "open") -> list[dict]:
    """
    GET /repos/{owner}/{repo}/issues?state={state}&per_page=100
    Paginates automatically. Excludes pull requests.
    """
    issues: list[dict] = []
    page   = 1
    while True:
        url = (f"https://api.github.com/repos/{full_name}/issues"
               f"?state={state}&per_page={API_PER_PAGE}&page={page}")
        try:
            resp = requests.get(url, headers=_github_headers(), timeout=15)
            if resp.status_code in (403, 429):
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                time.sleep(max(reset - int(time.time()), 5))
                continue
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            # Filter out pull requests
            issues.extend(i for i in batch if "pull_request" not in i)
            if len(batch) < API_PER_PAGE:
                break
            page += 1
            time.sleep(0.3)
        except requests.RequestException as e:
            log.error("Issue fetch error for %s: %s", full_name, e)
            break
    return issues


def upsert_repo_from_api(full_name: str, conn) -> Optional[int]:
    """
    Fetch a single repo from GitHub API and upsert into repositories.
    Returns repo_id on success, None on failure.
    """
    data = fetch_repo_from_api(full_name)
    if not data:
        return None

    owner, name = parse_owner_name(data["full_name"])
    html_url    = data.get("html_url") or f"https://github.com/{data['full_name']}"

    with conn.cursor() as cur:
        cur.execute(
            """
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
            """,
            {
                "github_id":   data["id"],
                "owner":       owner,
                "name":        name,
                "full_name":   data["full_name"],
                "description": (data.get("description") or "")[:2000] or None,
                "stars":       data.get("stargazers_count", 0),
                "forks":       data.get("forks_count", 0),
                "language":    (data.get("language") or "").lower() or None,
                "html_url":    html_url,
                "created_at":  data.get("created_at"),
            },
        )
        repo_id = cur.fetchone()[0]
        upsert_topics(conn, repo_id, data.get("topics") or [])
        conn.commit()

    log.info("Upserted repo %s -> repo_id=%d", full_name, repo_id)
    return repo_id


def upsert_issues_from_api(full_name: str, conn) -> int:
    """
    Fetch all open issues for a repo and upsert into issues + issue_labels.
    Returns count of issues processed.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT repo_id FROM repositories WHERE full_name = %s", (full_name,)
        )
        row = cur.fetchone()
    if not row:
        log.error("Repo %s not in DB — run upsert_repo_from_api first", full_name)
        return 0

    repo_id = row[0]
    issues  = fetch_issues_from_api(full_name, state="open")
    log.info("Fetched %d issues for %s", len(issues), full_name)

    if not issues:
        return 0

    values = [
        (
            iss["id"],                                     # github_issue_id
            repo_id,
            iss["title"][:500],
            (iss.get("body") or "")[:10000] or None,
            iss.get("state", "open"),
            iss.get("html_url"),
            iss.get("created_at"),
            iss.get("updated_at"),
        )
        for iss in issues
    ]

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO issues
                (github_issue_id, repo_id, title, body, state,
                 github_url, created_at, updated_at)
            VALUES %s
            ON CONFLICT (github_issue_id) DO UPDATE SET
                title      = EXCLUDED.title,
                body       = EXCLUDED.body,
                state      = EXCLUDED.state,
                github_url = EXCLUDED.github_url,
                updated_at = EXCLUDED.updated_at
            RETURNING issue_id, github_issue_id
            """,
            values,
            page_size=200,
            fetch=True,
        )
        returned = {gid: iid for iid, gid in cur.fetchall()}

        # Insert labels
        for iss in issues:
            issue_id = returned.get(iss["id"])
            if issue_id:
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

    log.info("Upserted %d issues for %s", len(values), full_name)
    return len(values)


# ──────────────────────────────────────────────────────────────
# PIPELINES
# ──────────────────────────────────────────────────────────────
def run_kaggle_pipeline(path: str = KAGGLE_JSON) -> None:
    """End-to-end: load -> clean -> validate -> upsert."""
    raw_df     = load_kaggle_dataset(path)
    cleaned_df = clean_dataset(raw_df)
    valid_df   = validate_and_fix(cleaned_df)

    conn = get_connection()
    try:
        insert_repositories(valid_df, conn)
    finally:
        conn.close()

    log.info("Kaggle pipeline complete. %d repos processed.", len(valid_df))


def run_api_sync(repo_list: list[str]) -> None:
    """
    Sync a list of repos (full_name strings like 'pallets/flask') from GitHub API.
    Fetches repo metadata + open issues for each.
    """
    conn = get_connection()
    try:
        for full_name in repo_list:
            rid = upsert_repo_from_api(full_name, conn)
            if rid:
                upsert_issues_from_api(full_name, conn)
            time.sleep(1)   # rate-limit courtesy
    finally:
        conn.close()

    log.info("API sync complete for %d repos.", len(repo_list))


# ──────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    """
    Usage examples (run from DBMS_database\DB\):

      # Load Kaggle data (reads DBMS_database\repos_folder\repos.json)
      python Py_file.py

      # Sync specific repos from GitHub API (+ their issues)
      python Py_file.py api pallets/flask facebook/react torvalds/linux
    """

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        repos = sys.argv[2:]
        if not repos:
            print("Usage: python Py_file.py api owner/repo [owner/repo ...]")
            sys.exit(1)
        run_api_sync(repos)
    else:
        run_kaggle_pipeline(KAGGLE_JSON)
