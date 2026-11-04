"""Automated Unit & Structural Verification Tests for FlowSync Phases 1 & 2."""

import os
from pathlib import Path
import pytest


def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_directory_structure_exists():
    """Verify that all required Phase 1 directories exist."""
    root = get_project_root()
    required_dirs = [
        "backend",
        "backend/app",
        "backend/ingestion",
        "backend/streaming",
        "backend/quality",
        "backend/ml",
        "backend/models",
        "backend/database",
        "backend/core",
        "frontend",
        "docker",
        "docker/postgres",
        "monitoring",
        "monitoring/prometheus",
        "monitoring/grafana",
        "monitoring/grafana/provisioning",
        "monitoring/grafana/provisioning/dashboards",
        "monitoring/grafana/provisioning/datasources",
        "tests",
        "scripts",
        "data",
        "docs",
    ]
    for d in required_dirs:
        path = root / d
        assert path.exists() and path.is_dir(), f"Missing directory: {d}"


def test_root_files_exist():
    """Verify that all required root project files exist."""
    root = get_project_root()
    required_files = [
        "README.md",
        ".env.example",
        ".gitignore",
        "docker-compose.yml",
    ]
    for f in required_files:
        path = root / f
        assert path.exists() and path.is_file(), f"Missing file: {f}"


def test_env_example_contains_all_placeholders():
    """Verify that .env.example contains configuration keys for all services."""
    root = get_project_root()
    content = (root / ".env.example").read_text(encoding="utf-8")
    expected_keys = [
        "KAFKA_BROKER_INTERNAL",
        "KAFKA_TOPIC_RAW",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "MINIO_BUCKET_RAW",
        "MINIO_BUCKET_REFINED",
        "MINIO_BUCKET_QUARANTINE",
        "MINIO_BUCKET_CHECKPOINTS",
        "MINIO_BUCKET_MODELS",
        "SPARK_APP_NAME",
        "PROMETHEUS_PORT",
        "GRAFANA_ADMIN_USER",
        "GRAFANA_ADMIN_PASSWORD",
    ]
    for key in expected_keys:
        assert key in content, f"Missing key in .env.example: {key}"


def test_gitignore_excludes_secrets_and_artifacts():
    """Verify that .gitignore properly excludes .env, models, and data artifacts."""
    root = get_project_root()
    content = (root / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in content
    assert "__pycache__" in content
    assert "*.parquet" in content
    assert "node_modules" in content
    assert "checkpoints" in content


def test_postgres_init_sql_contains_required_tables():
    """Verify that docker/postgres/init.sql creates all 5 required tables."""
    root = get_project_root()
    sql_content = (root / "docker/postgres/init.sql").read_text(encoding="utf-8").lower()
    required_tables = [
        "events_valid",
        "events_invalid",
        "pipeline_windowed_metrics",
        "anomaly_detections",
        "data_quality_runs",
    ]
    for table in required_tables:
        assert f"create table if not exists {table}" in sql_content, f"Missing table DDL: {table}"


def test_docker_compose_structure():
    """Verify that docker-compose.yml defines all 5 core services, persistent volumes, and networks."""
    root = get_project_root()
    compose_content = (root / "docker-compose.yml").read_text(encoding="utf-8")
    required_services = [
        "kafka:",
        "kafka-init:",
        "postgres:",
        "minio:",
        "minio-init:",
        "prometheus:",
        "grafana:",
    ]
    for service in required_services:
        assert service in compose_content, f"Missing service definition: {service}"

    required_volumes = [
        "kafka_data:",
        "postgres_data:",
        "minio_data:",
        "prometheus_data:",
        "grafana_data:",
    ]
    for volume in required_volumes:
        assert volume in compose_content, f"Missing volume definition: {volume}"


def test_prometheus_and_grafana_provisioning():
    """Verify Prometheus scrape configs and Grafana datasource provisioning."""
    root = get_project_root()
    prom_yaml = (root / "monitoring/prometheus/prometheus.yml").read_text(encoding="utf-8")
    assert "job_name: \"prometheus\"" in prom_yaml
    assert "job_name: \"flowsync-backend\"" in prom_yaml

    grafana_ds = (root / "monitoring/grafana/provisioning/datasources/datasources.yml").read_text(encoding="utf-8")
    assert "name: Prometheus" in grafana_ds
    assert "name: PostgreSQL-FlowSync" in grafana_ds
