"""FlowSync - Ingestion Command Line Interface (CLI).

Commands for running real-time synthetic data generation, batch CSV ingest,
and inspecting Kafka infrastructure connectivity.
"""

from __future__ import annotations

import argparse
import sys
import time

from confluent_kafka.admin import AdminClient

from core.config import get_settings
from ingestion.csv_ingest import CsvIngestionEngine
from ingestion.generator import GeneratorConfig, SyntheticEventGenerator
from ingestion.producer import KafkaEventProducer


def cmd_generate(args):
    """Run real-time synthetic generator."""
    settings = get_settings()
    producer = KafkaEventProducer(
        bootstrap_servers=args.bootstrap or settings.KAFKA_BROKER_EXTERNAL,
        client_id="flowsync-cli-generator",
    )
    config = GeneratorConfig(
        num_devices=args.devices,
        events_per_second=args.rate,
        corruption_rate=args.corruption,
        anomaly_rate=args.anomaly,
        target_topic=args.topic or settings.KAFKA_TOPIC_RAW,
    )
    generator = SyntheticEventGenerator(config=config, producer=producer)
    print(f"Starting FlowSync synthetic generator:")
    print(f"  Target Topic:    {config.target_topic}")
    print(f"  Devices:         {config.num_devices}")
    print(f"  Rate:            {config.events_per_second} events/sec")
    print(f"  Corruption Rate: {config.corruption_rate * 100:.1f}%")
    print(f"  Anomaly Rate:    {config.anomaly_rate * 100:.1f}%")
    print("Press Ctrl+C to stop.\n")

    generator.start()
    start_time = time.time()
    try:
        while True:
            time.sleep(2.0)
            st = generator.status()
            prod_st = producer.stats()
            print(
                f"[Runtime: {int(time.time() - start_time)}s] Generated: {st['generated_count']} "
                f"| Corruptions: {st['corruptions_count']} | Anomalies: {st['anomalies_count']} "
                f"| Delivered: {prod_st['delivered_count']} | DLQ: {prod_st['dlq_count']}"
            )
            if args.duration and (time.time() - start_time) >= args.duration:
                print(f"\nReached specified duration limit ({args.duration}s). Stopping...")
                break
    except KeyboardInterrupt:
        print("\nReceived interrupt. Stopping generator...")
    finally:
        generator.stop()
        print("Generator stopped cleanly.")


def cmd_csv(args):
    """Run CSV ingestion on specified file."""
    settings = get_settings()
    producer = KafkaEventProducer(
        bootstrap_servers=args.bootstrap or settings.KAFKA_BROKER_EXTERNAL,
        client_id="flowsync-cli-csv",
    )
    engine = CsvIngestionEngine(
        producer=producer,
        target_topic=args.topic or settings.KAFKA_TOPIC_RAW,
        dlq_topic=settings.KAFKA_TOPIC_DLQ,
    )
    print(f"Ingesting CSV file: {args.file}")
    res = engine.ingest_file(args.file)
    print("\n--- Ingestion Result ---")
    print(f"Total Rows:     {res.total_rows}")
    print(f"Valid Rows:     {res.valid_rows}")
    print(f"Rejected Rows:  {res.rejected_rows}")
    print(f"Duration:       {res.execution_time_seconds}s")
    print("------------------------")


def cmd_check_kafka(args):
    """Verify Kafka broker reachability and list cluster topics."""
    settings = get_settings()
    broker = args.bootstrap or settings.KAFKA_BROKER_EXTERNAL
    print(f"Checking Kafka connectivity at {broker}...")
    try:
        admin = AdminClient({"bootstrap.servers": broker, "socket.timeout.ms": 3000})
        metadata = admin.list_topics(timeout=5.0)
        print(f"[OK] Successfully connected to Kafka cluster.")
        print(f"Cluster Brokers: {[b.id for b in metadata.brokers.values()]}")
        print("Discovered Topics:")
        for topic_name, topic_data in sorted(metadata.topics.items()):
            p_count = len(topic_data.partitions)
            print(f"  - {topic_name:25} ({p_count} partitions)")
    except Exception as exc:
        print(f"[FAIL] Kafka check failed: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="FlowSync Telemetry Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: generate
    p_gen = subparsers.add_parser("generate", help="Run synthetic event generator")
    p_gen.add_argument("--rate", type=float, default=10.0, help="Events per second")
    p_gen.add_argument("--devices", type=int, default=10, help="Number of simulated devices")
    p_gen.add_argument("--corruption", type=float, default=0.05, help="Corruption probability [0.0-1.0]")
    p_gen.add_argument("--anomaly", type=float, default=0.05, help="Anomaly probability [0.0-1.0]")
    p_gen.add_argument("--duration", type=int, default=None, help="Execution duration in seconds")
    p_gen.add_argument("--topic", type=str, default=None, help="Kafka target topic")
    p_gen.add_argument("--bootstrap", type=str, default=None, help="Kafka bootstrap servers")
    p_gen.set_defaults(func=cmd_generate)

    # Subcommand: csv
    p_csv = subparsers.add_parser("csv", help="Ingest a CSV telemetry file")
    p_csv.add_argument("--file", type=str, required=True, help="Path to CSV dataset file")
    p_csv.add_argument("--topic", type=str, default=None, help="Kafka target topic")
    p_csv.add_argument("--bootstrap", type=str, default=None, help="Kafka bootstrap servers")
    p_csv.set_defaults(func=cmd_csv)

    # Subcommand: check-kafka
    p_chk = subparsers.add_parser("check-kafka", help="Check Kafka brokers and topic health")
    p_chk.add_argument("--bootstrap", type=str, default=None, help="Kafka bootstrap servers")
    p_chk.set_defaults(func=cmd_check_kafka)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

