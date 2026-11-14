"""
AstroHealth Anomaly Detection Module
Leverages Scikit-Learn Isolation Forest to detect unusual biometric telemetry patterns
by comparing real-time sensor streams against individualized physiological baselines,
accounting for motion context and measurement quality.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger("astrohealth.ai.anomaly")

FEATURE_NAMES = [
    "heart_rate",
    "hrv",
    "spo2",
    "body_temp",
    "motion_magnitude",
    "delta_hr",
    "delta_spo2",
    "delta_temp",
    "measurement_quality"
]


class AnomalyDetector:
    """
    Multivariate biometric anomaly detector using Isolation Forest.
    Trained on aerospace normative data and calibrated against crew baselines.
    """
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = contamination
        self.model_version = "astrohealth-isoforest-v1.2"
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False
        self._history_cache: Dict[str, List[bool]] = {}  # Tracks repeated anomalies per astronaut
        self._initialize_baseline_model()

    def _generate_synthetic_normative_data(self, n_samples: int = 1500) -> np.ndarray:
        """Generates normative aerospace physiological dataset for initial model calibration."""
        np.random.seed(42)
        # Resting state normal distribution
        hr = np.random.normal(64.0, 5.0, n_samples)
        hrv = np.random.normal(70.0, 8.0, n_samples)
        spo2 = np.random.normal(98.5, 0.7, n_samples)
        temp = np.random.normal(36.75, 0.18, n_samples)
        motion = np.random.exponential(0.08, n_samples)
        delta_hr = hr - 64.0
        delta_spo2 = spo2 - 98.5
        delta_temp = temp - 36.75
        quality = np.random.uniform(0.92, 1.0, n_samples)

        X = np.column_stack([
            hr, hrv, spo2, temp, motion,
            delta_hr, delta_spo2, delta_temp, quality
        ])
        return X

    def _initialize_baseline_model(self):
        """Fit Isolation Forest model with normative baseline distribution."""
        X_train = self._generate_synthetic_normative_data()
        self.model.fit(X_train)
        self.is_fitted = True
        logger.info(f"Isolation Forest model initialized and fitted with {len(X_train)} samples.")

    def extract_features(self, reading: Dict[str, Any], baseline_vitals: Optional[Dict[str, float]] = None) -> np.ndarray:
        """Converts raw sensor reading and astronaut baselines into feature vector."""
        base_hr = baseline_vitals.get("resting_heart_rate", 64.0) if baseline_vitals else 64.0
        base_spo2 = baseline_vitals.get("baseline_spo2", 98.4) if baseline_vitals else 98.4
        base_temp = baseline_vitals.get("baseline_body_temp", 36.75) if baseline_vitals else 36.75

        hr = float(reading.get("heart_rate", base_hr))
        hrv = float(reading.get("hrv", 70.0))
        spo2 = float(reading.get("spo2", base_spo2))
        temp = float(reading.get("body_temp", base_temp))
        motion = float(reading.get("motion_magnitude", 0.05))
        quality = float(reading.get("measurement_quality", 0.98))

        delta_hr = hr - base_hr
        delta_spo2 = spo2 - base_spo2
        delta_temp = temp - base_temp

        features = np.array([
            hr, hrv, spo2, temp, motion,
            delta_hr, delta_spo2, delta_temp, quality
        ]).reshape(1, -1)
        return features

    def predict(
        self, 
        reading: Dict[str, Any], 
        baseline_vitals: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Runs inference on live sensor reading.
        Returns anomaly classification, normalized anomaly score, and persistence evaluation.
        """
        if not self.is_fitted:
            self._initialize_baseline_model()

        X = self.extract_features(reading, baseline_vitals)
        
        # Isolation Forest prediction: -1 = anomaly, 1 = inlier/nominal
        pred = self.model.predict(X)[0]
        # Raw decision function score: lower = more anomalous
        raw_score = self.model.decision_function(X)[0]

        is_anomaly = bool(pred == -1)
        # Normalize score into range -1.0 (most anomalous) to +1.0 (most nominal)
        normalized_score = float(np.clip(raw_score * 3.5, -1.0, 1.0))
        
        # Calculate model confidence based on distance from decision boundary
        confidence = float(np.clip(0.5 + abs(raw_score) * 1.5, 0.55, 0.99))

        # Track anomaly persistence in rolling cache
        astro_id = reading.get("astronaut_id", "default")
        if astro_id not in self._history_cache:
            self._history_cache[astro_id] = []
        
        self._history_cache[astro_id].append(is_anomaly)
        # Keep last 10 readings in rolling window
        self._history_cache[astro_id] = self._history_cache[astro_id][-10:]
        
        # Persistent anomaly if >= 3 anomalies in the last 5 readings
        recent_window = self._history_cache[astro_id][-5:]
        is_persistent = sum(recent_window) >= 3

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(normalized_score, 4),
            "raw_decision_score": round(float(raw_score), 4),
            "confidence": round(confidence, 3),
            "data_quality_score": float(reading.get("measurement_quality", 0.98)),
            "is_persistent_anomaly": is_persistent,
            "recent_anomaly_count": sum(recent_window),
            "model_version": self.model_version
        }


# Global detector instance
anomaly_detector = AnomalyDetector()

