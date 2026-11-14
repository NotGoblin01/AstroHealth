"""
AstroHealth Artificial Intelligence & Analytics API Router
Provides endpoints for real-time anomaly detection, SHAP explainable AI,
cardiovascular trend analysis, behavioral health analytics, and trajectory forecasting.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

# Ensure ai_engine is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root / "ai_engine"))

from manager import ai_manager
from database import get_db
from models.schemas import (
    SensorReadingCreate,
    AIPredictionResponse
)

router = APIRouter(prefix="/api/ai", tags=["AI Analytics"])


@router.post("/predict", response_model=Dict[str, Any])
async def run_ai_prediction(
    reading_in: SensorReadingCreate,
    db = Depends(get_db)
):
    """
    Evaluates a live sensor reading using Isolation Forest anomaly detection
    and computes SHAP feature contributions explaining the prediction.
    """
    reading_dict = reading_in.model_dump()
    
    # Fetch astronaut baseline vitals if available
    astro = await db.astronauts.find_one({"astronaut_id": reading_in.astronaut_id})
    baseline = astro.get("baseline_vitals") if astro else None

    # Run AI inference and SHAP explanation
    result = ai_manager.analyze_reading(reading_dict, baseline)

    # Persist AI prediction in MongoDB
    pred_doc = result.copy()
    pred_doc["timestamp"] = datetime.now(timezone.utc)
    ins = await db.ai_predictions.insert_one(pred_doc)
    result["id"] = str(ins.inserted_id)

    return result


@router.get("/anomalies/{astronaut_id}")
async def list_recent_anomalies(
    astronaut_id: str,
    limit: int = Query(20, ge=1, le=100),
    db = Depends(get_db)
):
    """Retrieves recent detected biometric anomalies and their SHAP feature drivers."""
    cursor = db.ai_predictions.find(
        {"astronaut_id": astronaut_id, "is_anomaly": True}
    ).sort("timestamp", -1).limit(limit)

    anomalies = []
    async for a in cursor:
        a["id"] = str(a["_id"])
        if isinstance(a["timestamp"], datetime):
            a["timestamp"] = a["timestamp"].isoformat()
        anomalies.append(a)

    return anomalies


@router.get("/trends/cardiovascular/{astronaut_id}")
async def get_cardiovascular_trends(
    astronaut_id: str,
    limit: int = Query(60, ge=5, le=500),
    db = Depends(get_db)
):
    """
    Performs sliding-window cardiovascular analysis over recent telemetry.
    Calculates autonomic balance ratio, circadian deviation, and experimental risk score.
    """
    # Fetch historical readings
    cursor = db.sensor_readings.find(
        {"astronaut_id": astronaut_id}
    ).sort("timestamp", -1).limit(limit)

    readings = []
    async for r in cursor:
        readings.append(r)

    readings.reverse()  # Chronological order

    # Fetch baseline
    astro = await db.astronauts.find_one({"astronaut_id": astronaut_id})
    baseline = astro.get("baseline_vitals") if astro else None

    # Run analyzer
    trends = ai_manager.cardio_analyzer.analyze_trends(readings, baseline)
    return trends


@router.get("/trends/behavioral/{astronaut_id}")
async def get_behavioral_trends(
    astronaut_id: str,
    db = Depends(get_db)
):
    """
    Evaluates multi-day wellness records, cumulative sleep debt, and persistent fatigue patterns.
    """
    cursor = db.mental_health_logs.find(
        {"astronaut_id": astronaut_id}
    ).sort("date", 1)

    records = []
    async for r in cursor:
        records.append(r)

    analysis = ai_manager.behavioral_analyzer.analyze_wellness_records(records)
    return analysis


@router.get("/forecast/{astronaut_id}")
async def get_biometric_forecast(
    astronaut_id: str,
    metric_key: str = Query("heart_rate", pattern="^(heart_rate|hrv|spo2|body_temp)$"),
    horizon: int = Query(12, ge=3, le=30),
    db = Depends(get_db)
):
    """
    Statistically extrapolates future trend trajectory with 95% empirical confidence intervals.
    All estimated values are flagged with is_forecast: true.
    """
    cursor = db.sensor_readings.find(
        {"astronaut_id": astronaut_id}
    ).sort("timestamp", -1).limit(60)

    readings = []
    async for r in cursor:
        readings.append(r)

    readings.reverse()

    forecast_data = ai_manager.forecaster.forecast_biometric_indicator(
        readings=readings,
        metric_key=metric_key,
        horizon_steps=horizon,
        step_interval_seconds=120
    )
    return forecast_data


@router.get("/models")
async def get_active_ai_models():
    """Lists registered AI models, versions, and explainability capabilities."""
    return {
        "active_primary_model": ai_manager.active_model_name,
        "model_registry": ai_manager.model_registry,
        "supported_explainers": ["SHAP TreeExplainer (Surrogate RF)", "Decision Function Distance"],
        "disclaimer": "All models provide supportive aerospace health insights. Not clinically certified."
    }
