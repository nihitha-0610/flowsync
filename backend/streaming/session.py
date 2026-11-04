"""FlowSync - SparkSession Factory & S3A/MinIO Configuration.

Constructs tuned SparkSession with MinIO S3A storage credentials,
UTC timezone enforcement, and memory/shuffle optimizations.
"""

from __future__ import annotations

import os
from pyspark.sql import SparkSession


def get_spark_session(
    app_name: str = "FlowSyncStreamProcessor",
    master: str = "local[*]",
) -> SparkSession:
    """Build and configure the singleton SparkSession for structured streaming."""
    # MinIO S3A settings
    s3_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    if not s3_endpoint.startswith("http://") and not s3_endpoint.startswith("https://"):
        s3_endpoint = f"http://{s3_endpoint}"

    s3_access_key = os.getenv("MINIO_ROOT_USER", "flowsync_admin")
    s3_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "flowsync_minio_secret_key")

    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        # S3A / MinIO Filesystem Configuration
        .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", s3_access_key)
        .config("spark.hadoop.fs.s3a.secret.key", s3_secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        # Streaming & Execution Performance
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .config("spark.sql.session.timeZone", "UTC")
        # Parquet Output Optimization
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.parquet.writeLegacyFormat", "false")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

