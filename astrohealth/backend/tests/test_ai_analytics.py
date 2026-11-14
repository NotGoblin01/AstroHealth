"""
AstroHealth Phase 5 Test Suite
Tests Isolation Forest Anomaly Detection, SHAP Explainable AI,
Cardiovascular Trend Analytics, Behavioral Sleep Debt, and Health Trajectory Forecasting.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend and ai_engine to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root / "ai_engine"))

from anomaly_detector import anomaly_detector
from explainer import ExplainableAIEngine
from cardio_trends import cardio_analyzer
from behavioral_analytics import behavioral_analyzer
from forecaster import forecaster
from manager import ai_manager
from models.schemas import SensorReadingCreate
from routers import ai
from database import get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from seed import seed_database
    seed_database()

def test_anomaly_detection_nominal():
    """Verify Isolation Forest classifies nominal baseline biometrics as inliers."""
    nominal_reading = {
        "heart_rate": 64.0,
        "hrv": 72.0,
        "spo2": 98.6,
        "body_temp": 36.75,
        "motion_magnitude": 0.08,
        "measurement_quality": 0.98
    }
    baseline = {"resting_heart_rate": 62.0, "baseline_spo2": 98.4, "baseline_body_temp": 36.7}
    res = anomaly_detector.predict(nominal_reading, baseline)
    assert res["is_anomaly"] is False
    assert res["confidence"] > 0.60
    assert res["model_version"] == "astrohealth-isoforest-v1.2"

def test_anomaly_detection_severe_divergence():
    """Verify Isolation Forest flags acute hypoxia + compensatory tachycardia."""
    divergent_reading = {
        "heart_rate": 142.0,  # +80 bpm over baseline
        "hrv": 18.0,          # Autonomic collapse
        "spo2": 84.5,         # Severe hypoxia
        "body_temp": 37.4,
        "motion_magnitude": 0.04,  # Sedentary!
        "measurement_quality": 0.99
    }
    baseline = {"resting_heart_rate": 62.0, "baseline_spo2": 98.4, "baseline_body_temp": 36.7}
    res = anomaly_detector.predict(divergent_reading, baseline)
    assert res["is_anomaly"] is True
    assert res["anomaly_score"] < 0.0

def test_shap_explainability_attribution():
    """Verify SHAP produces quantitative feature contributions and readable observations."""
    explainer = ExplainableAIEngine(anomaly_detector)
    hypoxia_reading = {
        "astronaut_id": "ASTRO-001",
        "heart_rate": 138.0,
        "hrv": 20.0,
        "spo2": 85.0,
        "body_temp": 36.8,
        "motion_magnitude": 0.05,
        "measurement_quality": 0.98
    }
    baseline = {"resting_heart_rate": 62.0, "baseline_spo2": 98.4, "baseline_body_temp": 36.7}
    pred_result = anomaly_detector.predict(hypoxia_reading, baseline)
    
    explanation = explainer.explain(hypoxia_reading, pred_result, baseline)
    assert "contributing_features" in explanation
    assert len(explanation["contributing_features"]) >= 3
    
    # Check that SpO2 and Heart Rate are among top drivers
    driver_names = [f["feature_name"] for f in explanation["contributing_features"]]
    assert any("spo2" in n or "hr" in n for n in driver_names)

    # Check non-hallucinated clinical observation
    obs = explanation["clinical_observation"]
    assert "SpO2" in obs or "Heart rate" in obs or "Anomaly detected" in obs
    assert "Experimental" in explanation["experimental_disclaimer"]

def test_cardiovascular_trends():
    """Verify rolling cardiovascular slope and autonomic ratio calculation."""
    # Synthetic samples showing increasing heart rate
    sample_readings = [
        {"heart_rate": 62.0 + i*1.5, "hrv": 70.0 - i*1.2, "spo2": 98.5 - i*0.1, "body_temp": 36.7}
        for i in range(20)
    ]
    baseline = {"resting_heart_rate": 62.0, "resting_hrv": 70.0, "baseline_spo2": 98.5}
    trends = cardio_analyzer.analyze_trends(sample_readings, baseline)

    assert trends["status"] == "computed"
    assert trends["heart_rate"]["trend_direction"] == "increasing"
    assert trends["hrv"]["trend_direction"] == "decreasing"
    assert trends["autonomic_balance"]["tone"] == "sympathetic_dominant"
    assert trends["experimental_cardiovascular_risk"]["score"] > 20.0

def test_behavioral_sleep_analytics():
    """Verify behavioral health evaluation, sleep debt, and persistent strain flags."""
    sample_records = [
        {"date": "2026-04-01", "sleep_hours": 5.2, "stress_score": 8, "mood_score": 5, "fatigue_score": 8},
        {"date": "2026-04-02", "sleep_hours": 5.0, "stress_score": 8, "mood_score": 4, "fatigue_score": 8},
        {"date": "2026-04-03", "sleep_hours": 4.8, "stress_score": 9, "mood_score": 4, "fatigue_score": 9},
    ]
    res = behavioral_analyzer.analyze_wellness_records(sample_records)
    assert res["status"] == "computed"
    assert res["sleep_analysis"]["total_sleep_debt_hours"] > 8.0
    assert res["persistent_change_flags"]["persistent_high_stress"] is True
    assert res["persistent_change_flags"]["persistent_sleep_debt"] is True
    assert len(res["supportive_insights"]) >= 1

def test_health_trend_forecasting():
    """Verify statistical trajectory extrapolation and confidence bounds."""
    # 25 samples of steady heart rate
    sample_readings = [
        {"timestamp": datetime.now(timezone.utc).isoformat(), "heart_rate": 65.0 + (i * 0.4)}
        for i in range(25)
    ]
    forecast = forecaster.forecast_biometric_indicator(
        readings=sample_readings,
        metric_key="heart_rate",
        horizon_steps=10
    )
    assert forecast["status"] == "forecast_generated"
    assert len(forecast["forecast_points"]) == 10
    assert all(p["is_forecast"] is True for p in forecast["forecast_points"])
    assert all(p["is_measured"] is False for p in forecast["forecast_points"])
    assert forecast["trajectory_direction"] == "climbing"

@pytest.mark.anyio
async def test_ai_router_endpoints():
    """Verify API endpoints for AI prediction, models metadata, and trends."""
    db = await get_db()
    
    # 1. Models endpoint
    models_res = await ai.get_active_ai_models()
    assert "Isolation Forest" in models_res["active_primary_model"]

    # 2. Predict endpoint
    reading_in = SensorReadingCreate(
        astronaut_id="ASTRO-001",
        device_id="DEV-BIO-001",
        heart_rate=65.0,
        hrv=71.0,
        spo2=98.6,
        body_temp=36.75,
        activity_level="rest",
        measurement_quality=0.99
    )
    pred_res = await ai.run_ai_prediction(reading_in, db=db)
    assert "is_anomaly" in pred_res
    assert "confidence" in pred_res
    assert "clinical_observation" in pred_res
    assert "id" in pred_res  # Stored in DB

    # 3. Cardiovascular trends endpoint
    cardio_res = await ai.get_cardiovascular_trends("ASTRO-001", limit=30, db=db)
    assert cardio_res["status"] == "computed"
    assert "heart_rate" in cardio_res

    # 4. Forecast endpoint
    forecast_res = await ai.get_biometric_forecast("ASTRO-001", metric_key="heart_rate", horizon=8, db=db)
    assert forecast_res["status"] == "forecast_generated"
    assert len(forecast_res["forecast_points"]) == 8

