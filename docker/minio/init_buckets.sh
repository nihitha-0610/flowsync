#!/bin/bash
set -e

echo "Waiting for MinIO to be available at http://minio:9000..."
until curl -s http://minio:9000/minio/health/live; do
  echo "MinIO not ready yet. Retrying in 2 seconds..."
  sleep 2
done

echo "Configuring MinIO client alias..."
mc alias set myminio http://minio:9000 "${MINIO_ROOT_USER:-flowsync_admin}" "${MINIO_ROOT_PASSWORD:-flowsync_minio_secret_key}"

echo "Creating FlowSync S3 buckets (idempotent)..."
mc mb --ignore-existing myminio/flowsync-raw
mc mb --ignore-existing myminio/flowsync-refined
mc mb --ignore-existing myminio/flowsync-quarantine
mc mb --ignore-existing myminio/flowsync-checkpoints
mc mb --ignore-existing myminio/flowsync-models

echo "Listing provisioned MinIO buckets:"
mc ls myminio

echo "FlowSync MinIO bucket initialization completed successfully."
exit 0
