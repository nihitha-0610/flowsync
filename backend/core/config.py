"""FlowSync - Centralized System Settings & Configuration."""

import os
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and infrastructure configuration loaded from environment variables."""

    # Environment & Logging
    FLOWSYNC_ENV: str = "development"
    FLOWSYNC_DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Kafka
    KAFKA_BROKER_INTERNAL: str = "kafka:9092"
    KAFKA_BROKER_EXTERNAL: str = "localhost:9094"
    KAFKA_TOPIC_RAW: str = "events.raw"
    KAFKA_TOPIC_DLQ: str = "events.dlq"
    KAFKA_TOPIC_INVALID: str = "events.invalid"
    KAFKA_TOPIC_ANOMALIES: str = "events.anomalies"

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "flowsync_db"
    POSTGRES_USER: str = "flowsync_user"
    POSTGRES_PASSWORD: str = "flowsync_secure_password"
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://flowsync_user:flowsync_secure_password@localhost:5432/flowsync_db"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://flowsync_user:flowsync_secure_password@localhost:5432/flowsync_db"
    )

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "flowsync_admin"
    MINIO_ROOT_PASSWORD: str = "flowsync_minio_secret_key"
    MINIO_BUCKET_RAW: str = "flowsync-raw"
    MINIO_BUCKET_REFINED: str = "flowsync-refined"
    MINIO_BUCKET_QUARANTINE: str = "flowsync-quarantine"
    MINIO_BUCKET_CHECKPOINTS: str = "flowsync-checkpoints"
    MINIO_BUCKET_MODELS: str = "flowsync-models"

    # Spark
    SPARK_MASTER: str = "local[*]"
    SPARK_APP_NAME: str = "FlowSyncStreamProcessor"
    SPARK_CHECKPOINT_DIR: str = "s3a://flowsync-checkpoints/spark/telemetry_pipeline"

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton of Settings."""
    return Settings()
