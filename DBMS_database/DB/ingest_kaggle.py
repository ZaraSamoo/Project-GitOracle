from ingest import run_kaggle_pipeline, run_validation, get_connection


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "kaggle"

    if cmd == "kaggle":
        run_kaggle_pipeline()
    elif cmd == "validate":
        conn = get_connection()
        try:
            run_validation(conn)
        finally:
            conn.close()
    else:
        print("Usage: python ingest_kaggle.py [kaggle|validate]")
        sys.exit(1)
