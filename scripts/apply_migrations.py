"""FlowSync - Automatic Schema Migration Runner.

Executes pending SQL migrations in docker/postgres/migrations/ against PostgreSQL.
"""

import os
import sys
from pathlib import Path
import psycopg

# Load settings from core or environment
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "flowsync_db")
DB_USER = os.getenv("POSTGRES_USER", "flowsync_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "flowsync_secure_password")

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "docker" / "postgres" / "migrations"


def apply_migrations():
    """Apply all unapplied SQL migration files sequentially."""
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    try:
        with psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        ) as conn:
            with conn.cursor() as cur:
                # Ensure migration tracker exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(64) PRIMARY KEY,
                        applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("SELECT version FROM schema_migrations;")
                applied = {row[0] for row in cur.fetchall()}
                print(f"Previously applied migrations: {sorted(list(applied))}")

                migration_files = sorted(list(MIGRATIONS_DIR.glob("*.sql")))
                if not migration_files:
                    print("No migration files found.")
                    return

                for mfile in migration_files:
                    version = mfile.stem
                    if version in applied:
                        print(f"Skipping already applied migration: {version}")
                        continue

                    print(f"Applying migration: {version} ({mfile.name})...")
                    sql = mfile.read_text(encoding="utf-8")
                    cur.execute(sql)
                    cur.execute("INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING;", (version,))
                    print(f"Successfully applied: {version}")

        print("All migrations completed successfully.")
    except Exception as exc:
        print(f"Migration error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    apply_migrations()

