"""
AstroHealth Cardiovascular Trend Analysis Module
Evaluates continuous heart rate, heart rate variability (HRV), and pulse oximetry trends
to identify autonomic drift, cardiovascular deconditioning, and non-diagnostic risk indicators.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("astrohealth.ai.cardio")


class CardiovascularTrendAnalyzer:
    """
    Performs sliding-window statistical analysis over biometric time-series.
    Calculates autonomic tone, circadian variation, and experimental risk indices.
    """

    @staticmethod
    def analyze_trends(
        readings: List[Dict[str, Any]], 
        baseline_vitals: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes historical biometric samples (minimum 5 samples recommended).
        """
        if not readings or len(readings) < 3:
            return {
                "status": "insufficient_data",
                "message": "At least 3 biometric samples required for trend computation.",
                "sample_count": len(readings) if readings else 0
            }

        df = pd.DataFrame(readings)
        # Ensure numeric types
        for col in ["heart_rate", "hrv", "spo2", "body_temp"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["heart_rate", "spo2"])
        if len(df) < 3:
            return {"status": "insufficient_valid_data", "sample_count": len(df)}

        base_hr = baseline_vitals.get("resting_heart_rate", 64.0) if baseline_vitals else 64.0
        base_hrv = baseline_vitals.get("resting_hrv", 70.0) if baseline_vitals else 70.0
        base_spo2 = baseline_vitals.get("baseline_spo2", 98.4) if baseline_vitals else 98.4

        # Compute Statistical Metrics
        hr_series = df["heart_rate"].values
        hrv_series = df["hrv"].values if "hrv" in df.columns else np.array([base_hrv]*len(df))
        spo2_series = df["spo2"].values

        hr_mean = float(np.mean(hr_series))
        hr_std = float(np.std(hr_series))
        hr_min = float(np.min(hr_series))
        hr_max = float(np.max(hr_series))

        hrv_mean = float(np.mean(hrv_series))
        hrv_std = float(np.std(hrv_series))

        spo2_mean = float(np.mean(spo2_series))
        spo2_min = float(np.min(spo2_series))

        # Linear trend slopes (rate of change per sample)
        x = np.arange(len(df))
        hr_slope = float(np.polyfit(x, hr_series, 1)[0])
        hrv_slope = float(np.polyfit(x, hrv_series, 1)[0])
        spo2_slope = float(np.polyfit(x, spo2_series, 1)[0])

        # Autonomic Balance Ratio: higher HR combined with lower HRV reflects sympathetic overdrive
        # Normal ratio around 0.8 - 1.2
        autonomic_ratio = float((hr_mean / max(10.0, hrv_mean)) / (base_hr / max(10.0, base_hrv)))

        # Experimental Cardiovascular Stress / Risk Score (0 to 100)
        # Based on baseline deviations, slopes, and hypoxia risk
        hr_deviation = max(0.0, hr_mean - base_hr)
        hrv_suppression = max(0.0, base_hrv - hrv_mean)
        spo2_deficit = max(0.0, base_spo2 - spo2_mean)

        raw_risk = (hr_deviation * 0.9) + (hrv_suppression * 0.7) + (spo2_deficit * 6.0)
        if hr_slope > 0.5:
            raw_risk += 12.0  # Upward trending heart rate
        if spo2_slope < -0.3:
            raw_risk += 18.0  # Downward trending oxygenation

        risk_score = float(np.clip(raw_risk, 0.0, 100.0))

        risk_tier = "nominal"
        if risk_score > 65.0:
            risk_tier = "elevated_risk"
        elif risk_score > 35.0:
            risk_tier = "moderate_strain"

        return {
            "status": "computed",
            "sample_count": len(df),
            "heart_rate": {
                "mean": round(hr_mean, 1),
                "std": round(hr_std, 2),
                "min": round(hr_min, 1),
                "max": round(hr_max, 1),
                "trend_slope": round(hr_slope, 3),
                "trend_direction": "increasing" if hr_slope > 0.2 else ("decreasing" if hr_slope < -0.2 else "stable"),
                "baseline_deviation": round(hr_mean - base_hr, 1)
            },
            "hrv": {
                "mean": round(hrv_mean, 1),
                "std": round(hrv_std, 2),
                "trend_slope": round(hrv_slope, 3),
                "trend_direction": "increasing" if hrv_slope > 0.2 else ("decreasing" if hrv_slope < -0.2 else "stable"),
                "baseline_deviation": round(hrv_mean - base_hrv, 1)
            },
            "spo2": {
                "mean": round(spo2_mean, 1),
                "min": round(spo2_min, 1),
                "trend_slope": round(spo2_slope, 3),
                "trend_direction": "increasing" if spo2_slope > 0.1 else ("decreasing" if spo2_slope < -0.1 else "stable"),
                "baseline_deviation": round(spo2_mean - base_spo2, 1)
            },
            "autonomic_balance": {
                "ratio": round(autonomic_ratio, 2),
                "tone": "sympathetic_dominant" if autonomic_ratio > 1.3 else ("parasympathetic_recovery" if autonomic_ratio < 0.8 else "balanced")
            },
            "experimental_cardiovascular_risk": {
                "score": round(risk_score, 1),
                "tier": risk_tier,
                "disclaimer": "Experimental flight trend indicator. Non-diagnostic."
            }
        }


cardio_analyzer = CardiovascularTrendAnalyzer()

