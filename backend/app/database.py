"""FlowSync - Backend Database Client & Connection Manager."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "flowsync_db")
DB_USER = os.getenv("POSTGRES_USER", "flowsync_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "flowsync_secure_password")


def get_db_connection() -> psycopg.Connection:
    """Acquire a connection to PostgreSQL with dictionary rows."""
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row,
    )


def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute a read query and return dictionary rows."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


def execute_scalar(query: str, params: Optional[tuple] = None) -> Any:
    """Execute a query returning a single scalar result."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            if row:
                return list(row.values())[0]
            return None

