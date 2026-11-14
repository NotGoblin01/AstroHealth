"""
AstroHealth Telemetry Ingestion and Query Router
Handles high-throughput biometric and environmental sensor streams,
hardware safety threshold checks, validation, and real-time WebSocket broadcast.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from auth.security import get_current_user
from database import get_db
from services.websocket_service import broadcaster
from models.schemas import (
    SensorReadingCreate,
    SensorReadingResponse,
    EnvironmentalReadingCreate,
    EnvironmentalReadingResponse,
    AlertCategory,
    AlertStatus
)

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


async def check_biometric_safety_rules(reading: dict, db):
    """
    Evaluates independent clinical safety rules on ingested biometrics.
    Triggers safety alerts immediately if physiological parameters breach critical bounds.
    """
    alerts = []
    now_utc = datetime.now(timezone.utc)
    astro_id = reading["astronaut_id"]

    hr = reading["heart_rate"]
    spo2 = reading["spo2"]
    temp = reading["body_temp"]
    activity = reading.get("activity_level", "rest")

    # Critical Oxygen Saturation Check
    if spo2 < 88.0:
        alerts.append({
            "astronaut_id": astro_id,
            "source": "biometric",
            "category": AlertCategory.EMERGENCY.value,
            "title": "Severe Hypoxia Warning",
            "message": f"Critical blood oxygen drop detected: SpO2 {spo2:.1f}% (Threshold: < 88%). Immediate oxygen assessment required.",
            "vital_value": spo2,
            "threshold_value": 88.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })
    elif spo2 < 93.0:
        alerts.append({
            "astronaut_id": astro_id,
            "source": "biometric",
            "category": AlertCategory.ATTENTION_REQUIRED.value,
            "title": "Mild Desaturation Alert",
            "message": f"Blood oxygen below nominal mission threshold: SpO2 {spo2:.1f}%.",
            "vital_value": spo2,
            "threshold_value": 93.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })

    # Tachycardia / Bradycardia check
    if activity in ["rest", "sleep"]:
        if hr > 125.0:
            alerts.append({
                "astronaut_id": astro_id,
                "source": "biometric",
                "category": AlertCategory.URGENT_ASSESSMENT.value,
                "title": "Resting Tachycardia Alert",
                "message": f"Resting heart rate elevated: {hr:.1f} bpm during {activity} state.",
                "vital_value": hr,
                "threshold_value": 125.0,
                "status": AlertStatus.ACTIVE.value,
                "created_at": now_utc
            })
        elif hr < 40.0:
            alerts.append({
                "astronaut_id": astro_id,
                "source": "biometric",
                "category": AlertCategory.URGENT_ASSESSMENT.value,
                "title": "Severe Bradycardia Alert",
                "message": f"Heart rate critically depressed: {hr:.1f} bpm.",
                "vital_value": hr,
                "threshold_value": 40.0,
                "status": AlertStatus.ACTIVE.value,
                "created_at": now_utc
            })

    # Core/Body temperature checks
    if temp > 38.6:
        alerts.append({
            "astronaut_id": astro_id,
            "source": "biometric",
            "category": AlertCategory.ATTENTION_REQUIRED.value,
            "title": "Elevated Core Temperature",
            "message": f"Body temperature elevated to {temp:.2f}°C (Fever warning).",
            "vital_value": temp,
            "threshold_value": 38.6,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })
    elif temp < 35.0:
        alerts.append({
            "astronaut_id": astro_id,
            "source": "biometric",
            "category": AlertCategory.URGENT_ASSESSMENT.value,
            "title": "Hypothermia Warning",
            "message": f"Core body temperature dropped to {temp:.2f}°C.",
            "vital_value": temp,
            "threshold_value": 35.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })

    # Insert alerts and broadcast if triggered
    for alert in alerts:
        # Check if an unresolved active alert for this same title already exists in the last 15 minutes to prevent alert storms
        recent_cutoff = now_utc - timedelta(minutes=15)
        existing = await db.health_alerts.find_one({
            "astronaut_id": astro_id,
            "title": alert["title"],
            "status": "active",
            "created_at": {"$gte": recent_cutoff}
        })
        if not existing:
            ins = await db.health_alerts.insert_one(alert)
            alert["id"] = str(ins.inserted_id)
            await broadcaster.broadcast({
                "type": "health_alert",
                "alert": alert
            })


async def check_environmental_safety_rules(reading: dict, db):
    """Evaluates life support environmental safety rules (CO2, Radiation, Pressure)."""
    alerts = []
    now_utc = datetime.now(timezone.utc)
    comp = reading["compartment_id"]

    co2 = reading["co2_ppm"]
    rad_rate = reading["radiation_dose_rate_uSv_h"]
    pressure = reading["atmospheric_pressure"]

    # Carbon Dioxide concentration checks
    if co2 > 2500.0:
        alerts.append({
            "astronaut_id": "ALL_CREW",
            "source": "environmental",
            "category": AlertCategory.EMERGENCY.value,
            "title": f"Critical CO2 Accumulation in {comp}",
            "message": f"Carbon dioxide level critically elevated: {co2:.1f} ppm (Threshold: 2500 ppm). Initiate scrubber override.",
            "vital_value": co2,
            "threshold_value": 2500.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })
    elif co2 > 1200.0:
        alerts.append({
            "astronaut_id": "ALL_CREW",
            "source": "environmental",
            "category": AlertCategory.ATTENTION_REQUIRED.value,
            "title": f"Elevated CO2 in {comp}",
            "message": f"CO2 levels climbing: {co2:.1f} ppm. Verify scrubber air-flow circulation.",
            "vital_value": co2,
            "threshold_value": 1200.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })

    # Space Radiation Spike
    if rad_rate > 100.0:
        alerts.append({
            "astronaut_id": "ALL_CREW",
            "source": "environmental",
            "category": AlertCategory.EMERGENCY.value,
            "title": "Solar Particle Event / High Radiation Surge",
            "message": f"Radiation dose rate spike: {rad_rate:.1f} µSv/h. Direct crew to storm shelter immediately.",
            "vital_value": rad_rate,
            "threshold_value": 100.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })
    elif rad_rate > 45.0:
        alerts.append({
            "astronaut_id": "ALL_CREW",
            "source": "environmental",
            "category": AlertCategory.ATTENTION_REQUIRED.value,
            "title": "Elevated Cosmic Radiation",
            "message": f"Elevated radiation flux detected: {rad_rate:.1f} µSv/h.",
            "vital_value": rad_rate,
            "threshold_value": 45.0,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })

    # Cabin Atmospheric Pressure
    if pressure < 94.0 or pressure > 108.0:
        alerts.append({
            "astronaut_id": "ALL_CREW",
            "source": "environmental",
            "category": AlertCategory.URGENT_ASSESSMENT.value,
            "title": f"Atmospheric Pressure Anomaly in {comp}",
            "message": f"Cabin pressure deviated: {pressure:.2f} kPa (Nominal: 101.3 kPa).",
            "vital_value": pressure,
            "threshold_value": 101.3,
            "status": AlertStatus.ACTIVE.value,
            "created_at": now_utc
        })

    for alert in alerts:
        recent_cutoff = now_utc - timedelta(minutes=15)
        existing = await db.health_alerts.find_one({
            "title": alert["title"],
            "status": "active",
            "created_at": {"$gte": recent_cutoff}
        })
        if not existing:
            ins = await db.health_alerts.insert_one(alert)
            alert["id"] = str(ins.inserted_id)
            await broadcaster.broadcast({
                "type": "health_alert",
                "alert": alert
            })


# -------------------------------------------------------------
# Biometrics Telemetry Endpoints
# -------------------------------------------------------------
@router.post("/biometrics", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
async def ingest_biometric_reading(
    reading_in: SensorReadingCreate,
    db = Depends(get_db)
):
    """
    Ingests live wearable sensor readings (MAX30102, MPU6050, DS18B20).
    Validates range, applies safety rules, stores in MongoDB, and streams via WebSocket.
    """
    # Range validations
    if reading_in.heart_rate < 20.0 or reading_in.heart_rate > 280.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Heart rate {reading_in.heart_rate} bpm is outside physiological sensor bounds (20-280 bpm)."
        )
    if reading_in.spo2 < 40.0 or reading_in.spo2 > 100.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"SpO2 {reading_in.spo2}% is outside valid pulse oximetry range (40-100%)."
        )
    if reading_in.body_temp < 25.0 or reading_in.body_temp > 46.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Body temperature {reading_in.body_temp}°C is outside valid sensor range (25-46°C)."
        )

    reading_dict = reading_in.model_dump()
    
    # Compute 3-axis motion magnitude if not provided
    if reading_dict.get("motion_magnitude", 0.0) == 0.0:
        mx = reading_dict.get("motion_x", 0.0)
        my = reading_dict.get("motion_y", 0.0)
        mz = reading_dict.get("motion_z", 0.0)
        reading_dict["motion_magnitude"] = round(math.sqrt(mx*mx + my*my + mz*mz), 3)

    result = await db.sensor_readings.insert_one(reading_dict)
    reading_dict["id"] = str(result.inserted_id)

    # Check clinical safety rules
    await check_biometric_safety_rules(reading_dict, db)

    # Update device last_seen and online status
    if reading_dict.get("device_id"):
        await db.devices.update_one(
            {"device_id": reading_dict["device_id"]},
            {"$set": {"last_seen": reading_dict["timestamp"], "status": "online"}}
        )

    # Broadcast via WebSocket
    await broadcaster.broadcast({
        "type": "biometric_telemetry",
        "astronaut_id": reading_dict["astronaut_id"],
        "data": {
            "id": reading_dict["id"],
            "astronaut_id": reading_dict["astronaut_id"],
            "timestamp": reading_dict["timestamp"].isoformat(),
            "heart_rate": reading_dict["heart_rate"],
            "hrv": reading_dict["hrv"],
            "spo2": reading_dict["spo2"],
            "body_temp": reading_dict["body_temp"],
            "activity_level": reading_dict["activity_level"],
            "measurement_quality": reading_dict["measurement_quality"],
            "is_simulated": reading_dict["is_simulated"]
        }
    })

    return reading_dict


@router.post("/biometrics/batch", status_code=status.HTTP_201_CREATED)
async def ingest_biometric_batch(
    readings: List[SensorReadingCreate],
    db = Depends(get_db)
):
    """Batch ingestion endpoint for hardware buffering and offline synchronization."""
    if not readings:
        return {"status": "ok", "inserted_count": 0}

    docs = []
    for r in readings:
        doc = r.model_dump()
        if doc.get("motion_magnitude", 0.0) == 0.0:
            doc["motion_magnitude"] = round(math.sqrt(
                doc.get("motion_x", 0.0)**2 + doc.get("motion_y", 0.0)**2 + doc.get("motion_z", 0.0)**2
            ), 3)
        docs.append(doc)

    result = await db.sensor_readings.insert_many(docs)
    return {"status": "ok", "inserted_count": len(result.inserted_ids)}


@router.get("/biometrics/latest/{astronaut_id}", response_model=SensorReadingResponse)
async def get_latest_biometrics(
    astronaut_id: str,
    db = Depends(get_db)
):
    """Retrieve the most recent biometric telemetry reading for an astronaut."""
    reading = await db.sensor_readings.find_one(
        {"astronaut_id": astronaut_id},
        sort=[("timestamp", -1)]
    )
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No biometric telemetry found for astronaut {astronaut_id}."
        )
    reading["id"] = str(reading["_id"])
    return reading


@router.get("/biometrics/history/{astronaut_id}", response_model=List[SensorReadingResponse])
async def get_biometric_history(
    astronaut_id: str,
    limit: int = 60,
    minutes: Optional[int] = None,
    db = Depends(get_db)
):
    """
    Retrieve historical biometric time-series for chart rendering.
    Sorted in chronological order (earliest to latest) for graphs.
    """
    query: Dict[str, Any] = {"astronaut_id": astronaut_id}
    if isinstance(minutes, int) and minutes > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        query["timestamp"] = {"$gte": cutoff}

    actual_limit = limit if isinstance(limit, int) else 60
    cursor = db.sensor_readings.find(query).sort("timestamp", -1).limit(actual_limit)
    readings = []
    async for r in cursor:
        r["id"] = str(r["_id"])
        readings.append(r)

    # Reverse to return chronological order for charts
    readings.reverse()
    return readings


# -------------------------------------------------------------
# Environmental Telemetry Endpoints
# -------------------------------------------------------------
@router.post("/environmental", response_model=EnvironmentalReadingResponse, status_code=status.HTTP_201_CREATED)
async def ingest_environmental_reading(
    reading_in: EnvironmentalReadingCreate,
    db = Depends(get_db)
):
    """
    Ingests environmental pod readings (BME680, SCD41, Dosimeter).
    Validates thresholds, applies safety checks, stores in MongoDB, and streams via WebSocket.
    """
    reading_dict = reading_in.model_dump()
    result = await db.environmental_readings.insert_one(reading_dict)
    reading_dict["id"] = str(result.inserted_id)

    # Check life-support safety rules
    await check_environmental_safety_rules(reading_dict, db)

    # Broadcast via WebSocket
    await broadcaster.broadcast({
        "type": "environmental_telemetry",
        "compartment_id": reading_dict["compartment_id"],
        "data": {
            "id": reading_dict["id"],
            "compartment_id": reading_dict["compartment_id"],
            "timestamp": reading_dict["timestamp"].isoformat(),
            "temperature": reading_dict["temperature"],
            "humidity": reading_dict["humidity"],
            "atmospheric_pressure": reading_dict["atmospheric_pressure"],
            "co2_ppm": reading_dict["co2_ppm"],
            "voc_index": reading_dict["voc_index"],
            "radiation_dose_rate_uSv_h": reading_dict["radiation_dose_rate_uSv_h"],
            "radiation_cumulative_mSv": reading_dict["radiation_cumulative_mSv"],
            "is_simulated": reading_dict["is_simulated"]
        }
    })

    return reading_dict


@router.get("/environmental/latest", response_model=List[EnvironmentalReadingResponse])
async def get_latest_environmental(
    db = Depends(get_db)
):
    """Retrieve the latest environmental reading for each spacecraft compartment."""
    compartments = ["Command_Module", "Living_Quarters", "Science_Lab", "EVA_Airlock"]
    latest_readings = []
    
    for comp in compartments:
        reading = await db.environmental_readings.find_one(
            {"compartment_id": comp},
            sort=[("timestamp", -1)]
        )
        if reading:
            reading["id"] = str(reading["_id"])
            latest_readings.append(reading)

    return latest_readings


@router.get("/environmental/history/{compartment_id}", response_model=List[EnvironmentalReadingResponse])
async def get_environmental_history(
    compartment_id: str,
    limit: int = 60,
    db = Depends(get_db)
):
    """Retrieve historical atmospheric and radiation measurements for a compartment."""
    actual_limit = limit if isinstance(limit, int) else 60
    cursor = db.environmental_readings.find(
        {"compartment_id": compartment_id}
    ).sort("timestamp", -1).limit(actual_limit)

    readings = []
    async for r in cursor:
        r["id"] = str(r["_id"])
        readings.append(r)

    readings.reverse()
    return readings


@router.get("/summary")
async def get_telemetry_summary(db = Depends(get_db)):
    """System-wide telemetry summary for quick mission overview."""
    total_biometrics = await db.sensor_readings.count_documents({})
    total_environmental = await db.environmental_readings.count_documents({})
    total_devices = await db.devices.count_documents({})
    online_devices = await db.devices.count_documents({"status": "online"})
    active_alerts = await db.health_alerts.count_documents({"status": "active"})

    return {
        "total_biometric_samples": total_biometrics,
        "total_environmental_samples": total_environmental,
        "connected_hardware_devices": f"{online_devices}/{total_devices}",
        "active_health_alerts": active_alerts,
        "system_status": "NOMINAL" if active_alerts == 0 else "ATTENTION_REQUIRED"
    }
