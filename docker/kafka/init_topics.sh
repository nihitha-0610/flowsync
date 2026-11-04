#!/bin/bash
set -e

echo "Waiting for Kafka broker to be ready..."
until /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list; do
  echo "Kafka not ready yet. Retrying in 2 seconds..."
  sleep 2
done

echo "Creating FlowSync Kafka topics..."
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic events.raw --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic events.dlq --partitions 2 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic events.invalid --partitions 2 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic events.anomalies --partitions 2 --replication-factor 1

echo "Kafka topics verified:"
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

echo "FlowSync Kafka topic initialization completed successfully."
exit 0

