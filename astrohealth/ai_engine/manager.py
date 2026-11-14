"""
AstroHealth AI Lifecycle and Model Management Module
Orchestrates anomaly detection, explainability, model swapping, and pipeline versioning.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone

from anomaly_detector import anomaly_detector, AnomalyDetector
from explainer import ExplainableAIEngine
from cardio_trends import cardio_analyzer
from behavioral_analytics import behavioral_analyzer
from forecaster import forecaster

logger = logging.getLogger("astrohealth.ai.manager")


class AIEngineManager:
    """
    Centralized controller for the AstroHealth AI Analytics suite.
    Permits dynamic model swapping and hot-reloading.
    """
    def __init__(self):
        self.anomaly_detector: AnomalyDetector = anomaly_detector
        self.explainer: ExplainableAIEngine = ExplainableAIEngine(self.anomaly_detector)
        self.cardio_analyzer = cardio_analyzer
        self.behavioral_analyzer = behavioral_analyzer
        self.forecaster = forecaster
        self.active_model_name: str = "Isolation Forest (scikit-learn)"
        self.model_registry: Dict[str, Dict[str, Any]] = {
            "isolation_forest": {
                "name": "Isolation Forest",
                "version": "1.2.0",
                "type": "Unsupervised Multivariate Outlier Detector",
                "status": "active"
            },
            "random_forest_surrogate": {
                "name": "Random Forest Surrogate",
                "version": "1.0.0",
                "type": "SHAP Interpretable Tree Ensemble",
                "status": "active"
            },
            "polynomial_forecaster": {
                "name": "Polynomial Trend Extrapolator",
                "version": "1.1.0",
                "type": "Empirical Confidence Trajectory Forecaster",
                "status": "active"
            }
        }

    def analyze_reading(
        self, 
        reading: Dict[str, Any], 
        baseline_vitals: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Unified end-to-end inference and SHAP explainability pipeline.
        """
        # Step 1: Detect Anomaly
        pred_result = self.anomaly_detector.predict(reading, baseline_vitals)

        # Step 2: Explain with SHAP
        explanation = self.explainer.explain(reading, pred_result, baseline_vitals)

        now_utc = datetime.now(timezone.utc)
        astro_id = reading.get("astronaut_id", "ASTRO-UNKNOWN")

        return {
            "astronaut_id": astro_id,
            "timestamp": now_utc.isoformat(),
            "model_name": self.active_model_name,
            "model_version": self.anomaly_detector.model_version,
            "is_anomaly": explanation["is_anomaly"],
            "anomaly_score": explanation["anomaly_score"],
            "confidence": explanation["confidence"],
            "data_quality_score": pred_result["data_quality_score"],
            "is_persistent_anomaly": pred_result["is_persistent_anomaly"],
            "contributing_features": explanation["contributing_features"],
            "clinical_observation": explanation["clinical_observation"],
            "experimental_disclaimer": explanation["experimental_disclaimer"]
        }


ai_manager = AIEngineManager()

