"""Unit tests for FlowSync Multi-Device Synthetic Generator."""

import pytest
from core.event_contract import CanonicalTelemetryEvent
from ingestion.generator import GeneratorConfig, SyntheticEventGenerator


def test_generator_determinism():
    """Verify that identical seeds produce identical event sequences."""
    cfg1 = GeneratorConfig(num_devices=3, seed=12345, corruption_rate=0.0, anomaly_rate=0.0)
    gen1 = SyntheticEventGenerator(config=cfg1)
    batch1 = gen1.generate_batch(10)

    cfg2 = GeneratorConfig(num_devices=3, seed=12345, corruption_rate=0.0, anomaly_rate=0.0)
    gen2 = SyntheticEventGenerator(config=cfg2)
    batch2 = gen2.generate_batch(10)

    for (ev1, lbl1), (ev2, lbl2) in zip(batch1, batch2):
        assert lbl1 == lbl2
        # Compare physical values (timestamps will vary slightly unless overridden, check device and physics)
        assert ev1["device_id"] == ev2["device_id"]
        assert ev1["facility_id"] == ev2["facility_id"]
        assert ev1["temperature"] == ev2["temperature"]
        assert ev1["pressure"] == ev2["pressure"]


def test_generator_valid_events_contract():
    """Verify that uncorrupted events strictly satisfy the canonical contract."""
    cfg = GeneratorConfig(num_devices=5, seed=42, corruption_rate=0.0, anomaly_rate=0.2)
    gen = SyntheticEventGenerator(config=cfg)
    batch = gen.generate_batch(20)

    for payload, label in batch:
        # All uncorrupted events (even anomalies) MUST pass contract validation
        event = CanonicalTelemetryEvent(**payload)
        assert event.device_id.startswith("DEV-")
        assert event.facility_id.startswith("FAC-")
        assert event.timestamp.endswith("Z")
        assert -40.0 <= event.temperature <= 125.0
        assert 0.0 <= event.vibration <= 15.0


def test_generator_label_isolation():
    """Ensure ground truth synthetic label is returned separately and NOT inside the payload."""
    cfg = GeneratorConfig(num_devices=2, seed=99, corruption_rate=0.1, anomaly_rate=0.2)
    gen = SyntheticEventGenerator(config=cfg)
    batch = gen.generate_batch(15)

    for payload, label in batch:
        assert isinstance(label, str)
        if isinstance(payload, dict):
            assert "x-synthetic-label" not in payload
            assert "label" not in payload

