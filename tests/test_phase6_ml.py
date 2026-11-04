"""FlowSync - Phase 6 Machine Learning Anomaly Detection Tests.

Verifies feature extraction, model fitting, anomaly scoring, and explainability drivers.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from ml.model import FlowSyncAnomalyDetector, FEATURES


def test_feature_extraction():
    detector = FlowSyncAnomalyDetector()
    records = [
        {"temperature": 60.0, "vibration": 3.0, "pressure": 40.0, "flow_rate": 200.0, "power_consumption": 40.0},
        {"temperature": None, "vibration": 5.0, "pressure": None, "flow_rate": 150.0, "power_consumption": 30.0},
    ]
    X = detector.extract_features(records)
    assert X.shape == (2, 5)
    assert X[0, 0] == 60.0
    assert X[1, 0] == 0.0  # None imputed as 0.0


def test_training_and_explainability():
    detector = FlowSyncAnomalyDetector(contamination=0.1, n_estimators=50, random_state=42)
    detector.train([])
    assert detector.is_trained
    assert set(detector.baselines.keys()) == set(FEATURES)

    # Test nominal record
    nominal = [{
        "event_id": "11111111-1111-1111-1111-111111111111",
        "device_id": "DEV-0001",
        "timestamp": "2026-10-30T12:00:00Z",
        "temperature": 65.0,
        "vibration": 4.5,
        "pressure": 45.0,
        "flow_rate": 250.0,
        "power_consumption": 45.0,
    }]
    preds = detector.predict(nominal)
    assert len(preds) == 1
    assert "anomaly_score" in preds[0]
    assert "primary_driver" in preds[0]
    assert "feature_contributions" in preds[0]

    # Test extreme outlier record (extreme vibration)
    outlier = [{
        "event_id": "22222222-2222-2222-2222-222222222222",
        "device_id": "DEV-0002",
        "timestamp": "2026-10-30T12:00:01Z",
        "temperature": 65.0,
        "vibration": 14.9,  # Huge vibration spike
        "pressure": 45.0,
        "flow_rate": 250.0,
        "power_consumption": 45.0,
    }]
    outlier_preds = detector.predict(outlier)
    assert len(outlier_preds) == 1
    assert outlier_preds[0]["primary_driver"] == "vibration"

