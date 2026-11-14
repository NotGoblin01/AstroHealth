"""
AstroHealth Explainable AI (XAI) Module
Integrates SHAP (SHapley Additive exPlanations) to explain biometric anomaly detections,
attributing risk contributions to specific physiological features without clinical fabrication.
"""
import numpy as np
import logging
from typing import Dict, Any, List, Optional
import shap
from sklearn.ensemble import RandomForestClassifier

from anomaly_detector import FEATURE_NAMES, AnomalyDetector

logger = logging.getLogger("astrohealth.ai.xai")


class ExplainableAIEngine:
    """
    Computes SHAP feature attribution values for biometric anomalies.
    Translates mathematical game-theory Shapley values into readable aerospace clinical rationales.
    """
    def __init__(self, anomaly_detector: AnomalyDetector):
        self.anomaly_detector = anomaly_detector
        self.surrogate_rf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=6)
        self.explainer: Optional[shap.TreeExplainer] = None
        self._initialize_explainer()

    def _initialize_explainer(self):
        """Calibrates a surrogate tree-based explainer on normative and anomalous variations."""
        np.random.seed(42)
        X_norm = self.anomaly_detector._generate_synthetic_normative_data(n_samples=500)
        y_norm = np.zeros(len(X_norm))  # 0 = Nominal

        # Generate synthetic edge-case anomalies for surrogate contrast
        n_anom = 100
        hr_anom = np.concatenate([np.random.normal(125, 10, n_anom//2), np.random.normal(38, 4, n_anom//2)])
        hrv_anom = np.random.uniform(10, 25, n_anom)
        spo2_anom = np.random.uniform(82, 89, n_anom)
        temp_anom = np.concatenate([np.random.normal(38.8, 0.4, n_anom//2), np.random.normal(34.8, 0.3, n_anom//2)])
        motion_anom = np.random.uniform(0.01, 0.1, n_anom)
        d_hr = hr_anom - 64.0
        d_spo2 = spo2_anom - 98.5
        d_temp = temp_anom - 36.75
        quality = np.random.uniform(0.85, 1.0, n_anom)

        X_anom = np.column_stack([
            hr_anom, hrv_anom, spo2_anom, temp_anom, motion_anom,
            d_hr, d_spo2, d_temp, quality
        ])
        y_anom = np.ones(n_anom)  # 1 = Anomaly

        X_all = np.vstack([X_norm, X_anom])
        y_all = np.concatenate([y_norm, y_anom])

        self.surrogate_rf.fit(X_all, y_all)
        self.explainer = shap.TreeExplainer(self.surrogate_rf)
        logger.info("SHAP TreeExplainer calibrated on surrogate aerospace model.")

    def explain(
        self, 
        reading: Dict[str, Any], 
        prediction_result: Dict[str, Any],
        baseline_vitals: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes contributing features and human-readable explanation for a prediction.
        """
        X = self.anomaly_detector.extract_features(reading, baseline_vitals)
        
        feature_contributions = []
        try:
            # SHAP values for class 1 (Anomaly)
            shap_values = self.explainer.shap_values(X)
            
            # Handle shap API differences across versions (array shape [1, n_features, n_classes] or list of arrays)
            if isinstance(shap_values, list):
                vals = shap_values[1][0]  # Class 1
            elif len(shap_values.shape) == 3:
                vals = shap_values[0, :, 1]
            else:
                vals = shap_values[0]

            base_hr = baseline_vitals.get("resting_heart_rate", 64.0) if baseline_vitals else 64.0
            base_spo2 = baseline_vitals.get("baseline_spo2", 98.4) if baseline_vitals else 98.4
            base_temp = baseline_vitals.get("baseline_body_temp", 36.75) if baseline_vitals else 36.75

            baseline_map = {
                "heart_rate": base_hr,
                "hrv": 70.0,
                "spo2": base_spo2,
                "body_temp": base_temp,
                "motion_magnitude": 0.10,
                "delta_hr": 0.0,
                "delta_spo2": 0.0,
                "delta_temp": 0.0,
                "measurement_quality": 1.0
            }

            for idx, name in enumerate(FEATURE_NAMES):
                val = float(X[0, idx])
                shap_val = float(vals[idx])
                direction = "higher_risk" if shap_val > 0.0 else "protective_nominal"
                
                feature_contributions.append({
                    "feature_name": name,
                    "feature_value": round(val, 2),
                    "shap_value": round(shap_val, 4),
                    "contribution_direction": direction,
                    "baseline_value": round(baseline_map.get(name, 0.0), 2)
                })

            # Sort by absolute SHAP impact descending
            feature_contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        except Exception as e:
            logger.warning(f"SHAP explanation fallback: {e}")

        # Formulate non-fabricated clinical observation text
        observation_text = self._synthesize_observation(
            reading, prediction_result, feature_contributions, baseline_vitals
        )

        return {
            "is_anomaly": prediction_result["is_anomaly"],
            "anomaly_score": prediction_result["anomaly_score"],
            "confidence": prediction_result["confidence"],
            "contributing_features": feature_contributions[:5],  # Top 5 most impactful features
            "clinical_observation": observation_text,
            "experimental_disclaimer": (
                "Experimental aerospace AI indicator. Derived via Isolation Forest & SHAP. "
                "Not clinically validated for autonomous medical diagnosis."
            )
        }

    def _synthesize_observation(
        self,
        reading: Dict[str, Any],
        prediction_result: Dict[str, Any],
        contributions: List[Dict[str, Any]],
        baseline_vitals: Optional[Dict[str, float]]
    ) -> str:
        """Synthesizes factual, evidence-grounded observation without hallucination."""
        if not prediction_result["is_anomaly"]:
            return (
                "Multivariate biometric telemetry conforms within normative flight limits. "
                "Autonomic cardiovascular markers and core temperature align with crew baselines."
            )

        top_drivers = [c for c in contributions if c["contribution_direction"] == "higher_risk"][:2]
        driver_strings = []
        for d in top_drivers:
            name = d["feature_name"]
            val = d["feature_value"]
            base = d["baseline_value"]
            if "spo2" in name:
                driver_strings.append(f"SpO2 desaturation to {val:.1f}% (baseline: {base:.1f}%)")
            elif "hr" in name or "heart_rate" in name:
                driver_strings.append(f"Heart rate deviation to {val:.0f} bpm (baseline: {base:.0f} bpm)")
            elif "temp" in name:
                driver_strings.append(f"Core body temperature shift to {val:.2f}°C (baseline: {base:.2f}°C)")
            elif "hrv" in name:
                driver_strings.append(f"Suppressed autonomic HRV of {val:.0f} ms")

        drivers_summary = ", ".join(driver_strings) if driver_strings else "multivariate biometric divergence"
        
        persistence_note = "Repeated anomaly pattern observed across sliding window." if prediction_result.get("is_persistent_anomaly") else "Transient biometric deviation noted."

        return (
            f"Anomaly detected primarily driven by {drivers_summary}. "
            f"Measurement quality: {prediction_result['data_quality_score']*100:.0f}%. "
            f"{persistence_note}"
        )
