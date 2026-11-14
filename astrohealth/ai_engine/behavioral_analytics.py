"""
AstroHealth Behavioral Health & Circadian Analytics Module
Analyzes sleep architecture, psychological assessments, self-reported stress,
and cumulative fatigue trends to identify persistent psychological shifts.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger("astrohealth.ai.behavioral")


class BehavioralHealthAnalyzer:
    """
    Evaluates multi-day behavioral logs, sleep debt, and autonomic recovery.
    """

    @staticmethod
    def analyze_wellness_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes list of DailyWellness records (sorted chronologically).
        """
        if not records or len(records) == 0:
            return {
                "status": "no_records",
                "message": "No behavioral or wellness assessments logged."
            }

        df = pd.DataFrame(records)
        for col in ["mood_score", "stress_score", "sleep_hours", "sleep_quality_score", "fatigue_score", "workload_rating"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["sleep_hours", "stress_score"])
        if len(df) == 0:
            return {"status": "no_valid_data"}

        # Metrics computation
        sleep_mean = float(df["sleep_hours"].mean())
        sleep_min = float(df["sleep_hours"].min())
        sleep_debt = max(0.0, float((8.0 * len(df)) - df["sleep_hours"].sum()))

        stress_mean = float(df["stress_score"].mean())
        mood_mean = float(df["mood_score"].mean())
        fatigue_mean = float(df["fatigue_score"].mean())

        # Persistent Negative Trend Flags (3+ consecutive elevated stress or deficient sleep)
        recent = df.tail(3)
        persistent_high_stress = bool(len(recent) >= 3 and (recent["stress_score"] >= 7).all())
        persistent_sleep_debt = bool(len(recent) >= 3 and (recent["sleep_hours"] < 6.0).all())
        persistent_fatigue = bool(len(recent) >= 3 and (recent["fatigue_score"] >= 7).all())

        # Cumulative Behavioral Strain Index (0 to 100)
        # Factors: stress, low sleep, fatigue, low mood
        strain = (stress_mean * 3.5) + (fatigue_mean * 3.0) + (max(0, 8.0 - sleep_mean) * 5.0) + ((10.0 - mood_mean) * 2.0)
        if persistent_high_stress or persistent_sleep_debt:
            strain += 15.0

        strain_index = float(np.clip(strain, 0.0, 100.0))

        # Supportive Non-Diagnostic Guidance
        insights = []
        if persistent_sleep_debt:
            insights.append("Cumulative sleep debt detected over 3+ mission days. Recommend circadian lighting adjustment and 45-minute sleep hygiene extension.")
        if persistent_high_stress:
            insights.append("Sustained elevated stress index. Consider scheduling a private comms session with Flight Psychological Support.")
        if not insights:
            insights.append("Behavioral equilibrium and sleep-wake cycles remain aligned with mission parameters.")

        return {
            "status": "computed",
            "eval_days": len(df),
            "sleep_analysis": {
                "mean_duration_hours": round(sleep_mean, 1),
                "minimum_duration_hours": round(sleep_min, 1),
                "total_sleep_debt_hours": round(sleep_debt, 1),
                "status": "optimal" if sleep_mean >= 7.0 else ("mild_debt" if sleep_mean >= 6.0 else "severe_debt")
            },
            "psychological_metrics": {
                "mean_stress_score": round(stress_mean, 1),
                "mean_mood_score": round(mood_mean, 1),
                "mean_fatigue_score": round(fatigue_mean, 1)
            },
            "persistent_change_flags": {
                "persistent_high_stress": persistent_high_stress,
                "persistent_sleep_debt": persistent_sleep_debt,
                "persistent_fatigue": persistent_fatigue
            },
            "behavioral_strain_index": {
                "score": round(strain_index, 1),
                "category": "nominal" if strain_index < 35.0 else ("moderate_strain" if strain_index < 65.0 else "high_strain")
            },
            "supportive_insights": insights,
            "disclaimer": "Behavioral analytics are non-diagnostic supportive metrics for crew wellness."
        }


behavioral_analyzer = BehavioralHealthAnalyzer()

