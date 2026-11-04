"""FlowSync - Spark Structured Streaming Application Entrypoint.

Orchestrates Kafka ingestion streams, multi-sink micro-batch processing,
tumbling window aggregations, Prometheus metrics server, and graceful shutdown.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time

from core.config import get_settings
from streaming.batch_processor import MicroBatchProcessor
from streaming.metrics import STREAM_ACTIVE_QUERIES, start_streaming_metrics_server
from streaming.parsing import parse_and_validate_telemetry_stream
from streaming.session import get_spark_session
from streaming.windows import WindowedMetricsProcessor, build_windowed_aggregations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("flowsync.streaming.main")


def main():
    settings = get_settings()
    logger.info("Initializing FlowSync Spark Structured Streaming application...")

    # 1. Start Prometheus metrics server
    metrics_port = int(os.getenv("STREAMING_METRICS_PORT", "8000"))
    start_streaming_metrics_server(port=metrics_port)

    # 2. Acquire tuned SparkSession
    master = os.getenv("SPARK_MASTER", "local[*]")
    spark = get_spark_session(app_name="FlowSyncStreamProcessor", master=master)
    logger.info("SparkSession acquired successfully (Master: %s, Version: %s)", master, spark.version)

    # Kafka connectivity parameters
    kafka_broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", settings.KAFKA_BROKER_INTERNAL)
    kafka_topic = os.getenv("KAFKA_TOPIC_RAW", settings.KAFKA_TOPIC_RAW)
    starting_offsets = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

    logger.info("Connecting to Kafka stream on %s [Topic: %s]...", kafka_broker, kafka_topic)

    # 3. Define raw Kafka ingestion stream
    kafka_stream_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_broker)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", starting_offsets)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", 5000)
        .load()
    )

    # 4. Query A: Raw Archive, Parsing, Valid & Quarantine Sinks (foreachBatch)
    batch_processor = MicroBatchProcessor()
    checkpoint_query_a = os.getenv(
        "CHECKPOINT_DIR_QUERY_A",
        f"s3a://{settings.MINIO_BUCKET_CHECKPOINTS}/spark/query_a_telemetry",
    )

    logger.info("Starting Query A: Telemetry Multi-Sink Processor...")
    query_a = (
        kafka_stream_df.writeStream.queryName("telemetry_stream_main")
        .foreachBatch(batch_processor.process_batch)
        .option("checkpointLocation", checkpoint_query_a)
        .trigger(processingTime="2 seconds")
        .start()
    )

    # 5. Query B: Tumbling Window Aggregations
    logger.info("Starting Query B: 1-Minute Tumbling Window Aggregations...")
    # Parse stream for windowed aggregation query
    parsed_valid_stream, _ = parse_and_validate_telemetry_stream(kafka_stream_df)
    windowed_stream = build_windowed_aggregations(parsed_valid_stream)

    window_processor = WindowedMetricsProcessor()
    checkpoint_query_b = os.getenv(
        "CHECKPOINT_DIR_QUERY_B",
        f"s3a://{settings.MINIO_BUCKET_CHECKPOINTS}/spark/query_b_windows",
    )

    query_b = (
        windowed_stream.writeStream.queryName("windowed_metrics_stream")
        .foreachBatch(window_processor.process_windowed_batch)
        .option("checkpointLocation", checkpoint_query_b)
        .trigger(processingTime="5 seconds")
        .start()
    )

    STREAM_ACTIVE_QUERIES.set(2)
    logger.info("Both streaming queries started successfully. Awaiting stream processing...")

    # 6. Graceful Termination Handling
    def shutdown_handler(signum, frame):
        logger.info("Received termination signal (%s). Stopping streaming queries cleanly...", signum)
        STREAM_ACTIVE_QUERIES.set(0)
        try:
            query_a.stop()
            query_b.stop()
            spark.stop()
        except Exception as exc:
            logger.error("Error during graceful shutdown: %s", exc)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Wait for queries to terminate
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()

