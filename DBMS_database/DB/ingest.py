from __future__ import annotations

import glob
import logging
import os
import time
from typing import Optional

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm
try:
    import ijson
except ImportError as error:
    raise ImportError("Install ijson: pip install ijson") from error

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
KAGGLE_DIR = os.path.join(BASE_DIR, "repos_folder")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "dbname": os.getenv("PG_DB", "Git_Oracle"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "574209"),
}

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
STREAM_JSON_MIN_BYTES = int(os.getenv("KAGGLE_STREAM_MIN_MB", "128")) * 1024 * 1024
STREAM_JSON_BATCH_ROWS = int(os.getenv("KAGGLE_STREAM_BATCH_ROWS", "3000"))
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "3"))
DB_CONNECT_RETRY_DELAY_SEC = float(os.getenv("DB_CONNECT_RETRY_DELAY_SEC", "2"))
TOPIC_ID_CACHE: dict[str, int] = {}


def get_connection() -> psycopg2.extensions.connection:
    last_error: Exception | None = None
    for attempt in range(1, DB_CONNECT_RETRIES + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError as error:
            last_error = error
            if attempt == DB_CONNECT_RETRIES:
                break
            log.warning(
                "DB connection failed (attempt %d/%d): %s. Retrying in %.1fs",
                attempt,
                DB_CONNECT_RETRIES,
                error,
                DB_CONNECT_RETRY_DELAY_SEC,
            )
            time.sleep(DB_CONNECT_RETRY_DELAY_SEC)
    raise RuntimeError("Unable to connect to PostgreSQL after retries.") from last_error

def _detect_kaggle_file(directory: str) -> str:
    """
    Auto-detects the Kaggle dataset file inside `directory`.
    Preference order: repos.json > *.json.gz > *.json > *.csv.gz > *.csv

    For this project the file should be:
      DBMS_database\repos_folder\repos.json
    """
    candidate_dirs = [
        directory,                              # caller-provided path
        os.path.join(BASE_DIR, "repos_folder"), # DBMS_database\DB\repos_folder
        os.path.join(ROOT_DIR, "repos_folder"), # DBMS_database\repos_folder (legacy)
    ]

    checked_paths: list[str] = []
    patterns = ["repos.json", "*.json.gz", "*.jsonl.gz", "*.json", "*.csv.gz", "*.csv"]

    for candidate_dir in candidate_dirs:
        if not os.path.isdir(candidate_dir):
            continue
        for pattern in patterns:
            found = sorted(glob.glob(os.path.join(candidate_dir, pattern)))
            if found:
                selected = found[0]
                log.info(
                    "Auto-detected Kaggle file using pattern '%s': %s (candidates=%d)",
                    pattern,
                    selected,
                    len(found),
                )
                return selected
            checked_paths.append(os.path.join(candidate_dir, pattern))

    raise FileNotFoundError(
        "No dataset file found in expected locations.\n"
        + "\n".join(f"- {path}" for path in checked_paths)
        + "\nPlace your Kaggle file as repos.json in DBMS_database/DB/repos_folder."
    )


def _peek_json_root_byte(path: str) -> Optional[bytes]:
    """First non-whitespace byte of the file after optional UTF-8 BOM."""
    with open(path, "rb") as f:
        chunk = f.read(65536).lstrip()
    if chunk.startswith(b"\xef\xbb\xbf"):
        chunk = chunk[3:].lstrip()
    if not chunk:
        return None
    return chunk[:1]


def _should_stream_json_array(path: str) -> bool:
    """True for large repos.json formatted as [...] — pandas would MemoryError."""
    try:
        file_size = os.path.getsize(path)
    except OSError:
        return False
    if file_size < STREAM_JSON_MIN_BYTES:
        return False
    low = path.lower()
    if not low.endswith(".json") or low.endswith(".jsonl"):
        return False
    byte0 = _peek_json_root_byte(path)
    return byte0 == b"["


def _iter_ijson_root_array(path: str):
    """Stream objects from JSON array root using ijson."""
    with open(path, "rb") as fp:
        yield from ijson.items(fp, "item")


def _ingest_large_json_array(path: str, conn) -> int:
    """
    Incremental load of a [...] repos.json too large for pandas.read_json.
    Rows are buffered to DataFrames before clean + upsert (same semantics as bulk load).
    """
    rows_total = 0
    batch_size = STREAM_JSON_BATCH_ROWS
    pending: list[dict] = []
    batches = tqdm(desc="Streaming Kaggle batches", unit="batch")
    try:
        for obj in _iter_ijson_root_array(path):
            if isinstance(obj, dict):
                pending.append(obj)
            if len(pending) >= batch_size:
                df = pd.DataFrame(pending)
                df = clean_kaggle_dataset(df)
                insert_kaggle_repos(df, conn)
                rows_total += len(pending)
                batches.update(1)
                pending.clear()
                del df
        if pending:
            df = pd.DataFrame(pending)
            df = clean_kaggle_dataset(df)
            insert_kaggle_repos(df, conn)
            rows_total += len(pending)
            batches.update(1)
            pending.clear()
            del df
        return rows_total
    finally:
        batches.close()


def load_kaggle_dataset_from_path(path: str) -> pd.DataFrame:
    """Load dataset into RAM (only for CSV / small-medium JSON files)."""
    log.info("Loading: %s", path)

    if path.endswith((".json.gz", ".jsonl.gz")):
        df = pd.read_json(path, lines=True, compression="infer")
    elif path.endswith(".json"):
        try:
            df = pd.read_json(path)  # JSON array  [{ ... }, ...]
            if df.ndim == 1:
                df = pd.read_json(path, lines=True)
        except ValueError:
            df = pd.read_json(path, lines=True)
    else:
        df = pd.read_csv(path, compression="infer", low_memory=False)

    log.info("Raw rows: %d  |  Columns: %s", len(df), list(df.columns))
    return df


def load_kaggle_dataset(directory: str) -> pd.DataFrame:
    """
    Load Kaggle dataset from directory into a single DataFrame.

    Prefer `run_kaggle_pipeline()` for ingestion: it streams very large repos.json [...]
    (default: >128MB) instead of pandas.read_json, which avoids MemoryError.
    """
    path = _detect_kaggle_file(directory)
    return load_kaggle_dataset_from_path(path)


def _extract_str(val) -> Optional[str]:
    if isinstance(val, dict):
        return val.get("name") or val.get("value") or None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return str(val).strip() or None


def _extract_topics(val) -> list[str]:
    if isinstance(val, dict):
        nodes = val.get("nodes", [])
        return [
            n["topic"]["name"]
            for n in nodes
            if isinstance(n, dict) and "topic" in n and isinstance(n["topic"], dict)
        ]
    if isinstance(val, list):
        return [str(t).strip() for t in val if t]
    if isinstance(val, str) and val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return []


def _safe_description(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:2000]


def clean_kaggle_dataset(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {
        "nameWithOwner": "full_name",
        "stargazerCount": "stars",
        "forkCount": "forks",
        "primaryLanguage": "language",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "description": "description",
        "isFork": "is_fork",
        "openIssueCount": "open_issues",
        "watchers": "watchers",
        "licenseInfo":      "license_name",
        "repositoryTopics": "topics",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "full_name" not in df.columns:
        raise ValueError("Dataset has no 'nameWithOwner' or 'full_name' column.")
    df = df[df["full_name"].notna()].copy()
    df["full_name"] = df["full_name"].astype(str).str.strip()
    df = df[df["full_name"].str.len() > 0]
    before_full_name_pattern = len(df)
    df = df[df["full_name"].str.match(r"^[^/\s]+/[^/\s]+$", na=False)]
    dropped_invalid_full_name = before_full_name_pattern - len(df)
    if dropped_invalid_full_name:
        log.warning(
            "Dropped %d rows due to invalid full_name format (expected owner/repo). Remaining=%d",
            dropped_invalid_full_name,
            len(df),
        )

    split = df["full_name"].str.split("/", n=1, expand=True)
    if split.shape[1] < 2:
        raise ValueError("Invalid 'full_name' values after filtering; expected owner/repo format.")
    df["owner"] = split[0].str.strip()
    df["name"] = split[1].str.strip()

    for col in ["stars", "forks"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)
        else:
            df[col] = 0
    for col in ["language", "license_name"]:
        if col in df.columns:
            df[col] = df[col].apply(_extract_str)
    if "topics" in df.columns:
        df["topics"] = df["topics"].apply(_extract_topics)
    else:
        df["topics"] = [[] for _ in range(len(df))]
    df["html_url"] = "https://github.com/" + df["owner"] + "/" + df["name"]

    for col in ["created_at", "updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    before = len(df)
    df = df.sort_values("stars", ascending=False).drop_duplicates(subset=["full_name"], keep="first")
    log.info("Deduplication removed %d rows. Remaining: %d", before - len(df), len(df))
    df = df[df["owner"].str.len() > 0]
    df = df[df["name"].str.len() > 0]
    df["topics"] = df["topics"].apply(lambda xs: sorted(set(t.strip().lower() for t in xs if str(t).strip())))
    return df.reset_index(drop=True)


def upsert_topics(conn, repo_id: int, topics: list[str], cur=None) -> None:
    if not topics:
        return
    if cur is None:
        with conn.cursor() as own_cur:
            upsert_topics(conn, repo_id, topics, own_cur)
        return
    if len(TOPIC_ID_CACHE) > 50000:
        TOPIC_ID_CACHE.clear()
        log.warning("TOPIC_ID_CACHE exceeded 50k entries; cache cleared.")
    for topic in topics:
        topic = topic.strip().lower()
        if not topic:
            continue
        topic_id = TOPIC_ID_CACHE.get(topic)
        if topic_id is None:
            cur.execute(
                """
                INSERT INTO repo_topics(name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING topic_id
                """,
                (topic,),
            )
            row = cur.fetchone()
            if not row:
                continue
            topic_id = row[0]
            TOPIC_ID_CACHE[topic] = topic_id
        cur.execute(
            """
            INSERT INTO repository_topics(repo_id, topic_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (repo_id, topic_id),
        )


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

def insert_kaggle_repos(df: pd.DataFrame, conn) -> None:
    total = len(df)
    log.info("Upserting %d Kaggle repos …", total)
    for start in tqdm(range(0, total, BATCH_SIZE), desc="Kaggle->DB"):
        batch = df.iloc[start: start + BATCH_SIZE]
        with conn.cursor() as cur:
            for _, row in batch.iterrows():
                repo_name_for_log = row.get("full_name")
                savepoint_name = "sp_repo_row"
                try:
                    cur.execute(f"SAVEPOINT {savepoint_name}")
                    params = {
                        "full_name": row["full_name"],
                        "owner": row["owner"],
                        "name": row["name"],
                        "description": _safe_description(row.get("description")),
                        "stars": int(row["stars"]),
                        "forks": int(row["forks"]),
                        "language": row.get("language"),
                        "html_url": row.get("html_url"),
                    }
                    cur.execute(_KAGGLE_UPSERT, params)
                    result = cur.fetchone()
                    if result:
                        upsert_topics(conn, result[0], row.get("topics") or [], cur=cur)
                    cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                except Exception as error:  # pylint: disable=broad-exception-caught
                    cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    cur.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    log.error("Failed to upsert repo '%s': %s", repo_name_for_log, error)
                    continue
        conn.commit()

    log.info("Kaggle upsert complete.")

VALIDATION_QUERIES = {
    "top_by_stars": """
        SELECT full_name, owner, name, stars, language, html_url
        FROM   repositories
        ORDER  BY stars DESC
        LIMIT  10;
    """,
    "repos_without_topics": """
        SELECT r.full_name, r.stars
        FROM   repositories
        LEFT JOIN repository_topics rt ON rt.repo_id = r.repo_id
        WHERE  rt.repo_id IS NULL
        ORDER BY r.stars DESC
        LIMIT  20;
    """,
    "top_topics": """
        SELECT t.name, COUNT(*) AS repo_count
        FROM repository_topics rt
        JOIN repo_topics t ON t.topic_id = rt.topic_id
        GROUP BY t.name
        ORDER BY repo_count DESC, t.name ASC
        LIMIT 20;
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


def run_kaggle_pipeline(kaggle_dir: str = KAGGLE_DIR) -> None:
    path = _detect_kaggle_file(kaggle_dir)
    conn = get_connection()
    try:
        if _should_stream_json_array(path):
            log.info(
                "Streaming large JSON array (>=%d MB): %s",
                STREAM_JSON_MIN_BYTES // (1024 * 1024),
                path,
            )
            rows_processed = _ingest_large_json_array(path, conn)
            log.info("Kaggle streaming pipeline complete. Rows processed (~): %s", rows_processed)
        else:
            df = load_kaggle_dataset_from_path(path)
            df = clean_kaggle_dataset(df)
            insert_kaggle_repos(df, conn)
            log.info("Kaggle pipeline done. %d repos upserted.", len(df))
    finally:
        conn.close()


def run_full_pipeline(kaggle_dir: str = KAGGLE_DIR) -> None:
    run_kaggle_pipeline(kaggle_dir)
    conn = get_connection()
    try:
        run_validation(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "kaggle"

    if cmd == "kaggle":
        run_kaggle_pipeline()

    elif cmd == "full":
        run_full_pipeline()

    elif cmd == "validate":
        conn = get_connection()
        try:
            run_validation(conn)
        finally:
            conn.close()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
