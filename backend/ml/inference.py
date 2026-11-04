"""FlowSync - Machine Learning Anomaly Inference Engine.

Performs real-time Isolation Forest scoring, persists detections to PostgreSQL,
and emits anomaly events to Kafka topic events.anomalies.
"""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import joblib
from minio import Minio
import psycopg

from ml.model import FlowSyncAnomalyDetector

logger = logging.getLogger("flowsync.ml.inference")

MODELS_DIR = Path(__file__).resolve().parent / "saved_models"
LOCAL_MODEL_PATH = MODELS_DIR / "isolation_forest_v1.joblib"


class AnomalyInferenceService:
    """Inference service executing Isolation Forest scoring on valid event streams."""

    def __init__(self, model: Optional[FlowSyncAnomalyDetector] = None):
        self.model = model or self._load_or_init_model()

    def _load_or_init_model(self) -> FlowSyncAnomalyDetector:
        """Load model from local disk, MinIO, or initialize a trained instance."""
        # 1. Try local disk
        if LOCAL_MODEL_PATH.exists():
            try:
                detector = joblib.load(LOCAL_MODEL_PATH)
                logger.info("Loaded model from local disk cache: %s", LOCAL_MODEL_PATH)
                return detector
            except Exception as exc:
                logger.warning("Failed loading local model (%s); falling back to MinIO", exc)

        # 2. Try MinIO
        try:
            endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000").replace("http://", "").replace("https://", "")
            access_key = os.getenv("MINIO_ROOT_USER", "flowsync_admin")
            secret_key = os.getenv("MINIO_ROOT_PASSWORD", "flowsync_minio_secret_key")
            minio_client = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False)
            bucket_name = os.getenv("MINIO_BUCKET_MODELS", "flowsync-models")

            response = minio_client.get_object(bucket_name, "isolation_forest/v1/model.joblib")
            buffer = io.BytesIO(response.read())
            response.close()
            response.release_conn()
            buffer.seek(0)
            detector = joblib.load(buffer)
            # cache locally
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(detector, LOCAL_MODEL_PATH)
            logger.info("Successfully fetched and cached model from MinIO")
            return detector
        except Exception as exc:
            logger.info("MinIO model not found (%s); initializing new model baseline", exc)

        # 3. Fallback: initialize and fit synthetic baseline
        detector = FlowSyncAnomalyDetector(contamination=0.05, n_estimators=100, random_state=42)
        detector.train([])
        try:
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(detector, LOCAL_MODEL_PATH)
        except Exception:
            pass
        return detector

    def score_and_record(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score incoming records and persist detected anomalies to PostgreSQL."""
        if not records:
            return []

        results = self.model.predict(records)
        anomalies = [r for r in results if r["is_anomaly"]]

        if not anomalies:
            logger.debug("Scored %d records: 0 anomalies detected.", len(records))
            return []

        logger.info("Scored %d records: %d anomalies detected!", len(records), len(anomalies))
        self._persist_anomalies_to_postgres(anomalies)
        return anomalies

    def _persist_anomalies_to_postgres(self, anomalies: List[Dict[str, Any]]):
        """Insert detected anomalies into PostgreSQL anomaly_detections table."""
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        dbname = os.getenv("POSTGRES_DB", "flowsync_db")
        user = os.getenv("POSTGRES_USER", "flowsync_user")
        password = os.getenv("POSTGRES_PASSWORD", "flowsync_secure_password")

        insert_sql = """
            INSERT INTO anomaly_detections (
                anomaly_id, event_id, device_id, timestamp,
                anomaly_score, confidence, is_anomaly, primary_driver,
                feature_contributions, detected_at
            ) VALUES (
                %(anomaly_id)s, %(event_id)s, %(device_id)s, %(timestamp)s,
                %(anomaly_score)s, %(confidence)s, %(is_anomaly)s, %(primary_driver)s,
                %(feature_contributions)s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (anomaly_id) DO NOTHING;
        """

        rows = []
        for a in anomalies:
            rows.append({
                "anomaly_id": str(uuid.uuid4()),
                "event_id": str(a["event_id"]) if a.get("event_id") else None,
                "device_id": a["device_id"],
                "timestamp": a["timestamp"],
                "anomaly_score": a["anomaly_score"],
                "confidence": a["confidence"],
                "is_anomaly": True,
                "primary_driver": a["primary_driver"],
                "feature_contributions": json.dumps(a["feature_contributions"]),
            })

        try:
            with psycopg.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                autocommit=True,
            ) as conn:
                with conn.cursor() as cur:
                    cur.executemany(insert_sql, rows)
            logger.info("Persisted %d anomalies to PostgreSQL anomaly_detections", len(rows))
        except Exception as exc:
            logger.error("Failed to persist anomalies to PostgreSQL: %s", exc)

