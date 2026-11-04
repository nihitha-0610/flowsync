"""FlowSync - Machine Learning Training Pipeline.

Trains Isolation Forest anomaly detection on historical valid telemetry,
computes explainability baselines, and persists model artifact to MinIO.
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
import joblib
from minio import Minio
import psycopg
from psycopg.rows import dict_row

from ml.model import FlowSyncAnomalyDetector

logger = logging.getLogger("flowsync.ml.train")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

MODELS_DIR = Path(__file__).resolve().parent / "saved_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_MODEL_PATH = MODELS_DIR / "isolation_forest_v1.joblib"


def get_minio_client() -> Minio:
    """Instantiate MinIO client using environment variables."""
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000").replace("http://", "").replace("https://", "")
    access_key = os.getenv("MINIO_ROOT_USER", "flowsync_admin")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "flowsync_minio_secret_key")
    return Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False)


def fetch_training_data(limit: int = 5000) -> list[dict]:
    """Query recent valid telemetry events from PostgreSQL."""
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    dbname = os.getenv("POSTGRES_DB", "flowsync_db")
    user = os.getenv("POSTGRES_USER", "flowsync_user")
    password = os.getenv("POSTGRES_PASSWORD", "flowsync_secure_password")

    records = []
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            row_factory=dict_row,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, device_id, timestamp, temperature,
                           vibration, pressure, flow_rate, power_consumption
                    FROM events_valid
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                records = cur.fetchall()
        logger.info("Fetched %d training records from events_valid", len(records))
    except Exception as exc:
        logger.warning("Could not query events_valid (%s); using synthetic baseline", exc)

    return records


def train_and_persist_model() -> FlowSyncAnomalyDetector:
    """Train Isolation Forest and persist model locally and to MinIO."""
    records = fetch_training_data()
    detector = FlowSyncAnomalyDetector(contamination=0.05, n_estimators=100, random_state=42)
    detector.train(records)

    # 1. Save locally
    joblib.dump(detector, LOCAL_MODEL_PATH)
    logger.info("Saved trained model locally to %s", LOCAL_MODEL_PATH)

    # 2. Upload to MinIO
    try:
        minio_client = get_minio_client()
        bucket_name = os.getenv("MINIO_BUCKET_MODELS", "flowsync-models")
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        buffer = io.BytesIO()
        joblib.dump(detector, buffer)
        buffer.seek(0)
        size = buffer.getbuffer().nbytes

        minio_client.put_object(
            bucket_name=bucket_name,
            object_name="isolation_forest/v1/model.joblib",
            data=buffer,
            length=size,
            content_type="application/octet-stream",
        )
        logger.info("Successfully uploaded model artifact to s3a://%s/isolation_forest/v1/model.joblib", bucket_name)
    except Exception as exc:
        logger.warning("MinIO upload skipped or failed: %s", exc)

    return detector


if __name__ == "__main__":
    train_and_persist_model()

