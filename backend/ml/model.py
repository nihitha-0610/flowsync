"""FlowSync - Machine Learning Anomaly Detection Model.

Implements Scikit-Learn IsolationForest wrapping, feature extraction,
min-max/z-score explainability attribution, and serialization.
"""

from __future__ import annotations

import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("flowsync.ml.model")

FEATURES = ["temperature", "vibration", "pressure", "flow_rate", "power_consumption"]


class FlowSyncAnomalyDetector:
    """Isolation Forest anomaly detector with multi-sensor explainability drivers."""

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
        )
        self.is_trained = False
        self.baselines: Dict[str, Dict[str, float]] = {}

    def extract_features(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """Extract and clean numeric features from record dictionaries."""
        df = pd.DataFrame(records)
        for col in FEATURES:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df[FEATURES].to_numpy()

    def train(self, records: List[Dict[str, Any]]):
        """Fit IsolationForest model and calculate feature baselines."""
        if len(records) < 10:
            logger.warning("Fewer than 10 records provided for training; generating synthetic normal baseline.")
            records = self._generate_synthetic_baseline(50)

        X = self.extract_features(records)
        self.model.fit(X)
        self.is_trained = True

        # Calculate baselines for explainability
        df = pd.DataFrame(X, columns=FEATURES)
        for col in FEATURES:
            mean_val = float(df[col].mean())
            std_val = float(df[col].std()) if float(df[col].std()) > 1e-4 else 1.0
            self.baselines[col] = {"mean": mean_val, "std": std_val}

        logger.info(
            "Trained IsolationForest model on %d records with contamination=%.2f",
            len(records),
            self.contamination,
        )

    def _generate_synthetic_baseline(self, n: int = 50) -> List[Dict[str, Any]]:
        """Generate nominal baseline telemetry for cold-start initialization."""
        rng = np.random.default_rng(self.random_state)
        records = []
        for _ in range(n):
            records.append({
                "temperature": float(rng.normal(65.0, 5.0)),
                "vibration": float(rng.normal(4.5, 0.8)),
                "pressure": float(rng.normal(45.0, 4.0)),
                "flow_rate": float(rng.normal(250.0, 20.0)),
                "power_consumption": float(rng.normal(45.0, 5.0)),
            })
        return records

    def predict(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score records and return anomaly classification with explainability metrics."""
        if not records:
            return []
        if not self.is_trained:
            logger.info("Model not trained yet; training on initial baseline before inference.")
            self.train(records)

        X = self.extract_features(records)
        # raw predictions: 1 = inlier, -1 = outlier
        preds = self.model.predict(X)
        # decision function: lower is more abnormal, invert for anomaly score
        raw_scores = -self.model.score_samples(X)

        results = []
        for i, r in enumerate(records):
            is_anomaly = bool(preds[i] == -1)
            raw_score = float(raw_scores[i])
            # normalize confidence to [0, 1]
            confidence = round(1.0 / (1.0 + np.exp(-raw_score * 5.0)), 4)

            # Feature explainability calculation: z-score distance from mean
            contributions: Dict[str, float] = {}
            max_driver = FEATURES[0]
            max_dev = -1.0

            for j, f in enumerate(FEATURES):
                base = self.baselines.get(f, {"mean": 0.0, "std": 1.0})
                dev = abs(X[i, j] - base["mean"]) / base["std"]
                contributions[f] = round(float(dev), 2)
                if dev > max_dev:
                    max_dev = dev
                    max_driver = f

            results.append({
                "event_id": r.get("event_id"),
                "device_id": r.get("device_id", "UNKNOWN"),
                "timestamp": r.get("timestamp"),
                "is_anomaly": is_anomaly,
                "anomaly_score": round(raw_score, 4),
                "confidence": confidence,
                "primary_driver": max_driver,
                "feature_contributions": contributions,
            })
        return results

