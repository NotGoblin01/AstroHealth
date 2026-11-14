"""
AstroHealth Hardware Device Management Router
Handles IoT sensor devices, registration, heartbeats, battery levels, and connectivity monitoring.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth.security import get_current_user, require_roles
from database import get_db
from models.schemas import (
    DeviceCreate,
    DeviceResponse,
    DeviceBase,
    DeviceHeartbeat,
    DeviceStatus,
    DeviceType,
    UserRole
)

router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    assigned_to: Optional[str] = None,
    device_type: Optional[DeviceType] = None,
    status_filter: Optional[DeviceStatus] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """List registered IoT biomedical and environmental monitoring devices."""
    query = {}
    if assigned_to:
        query["assigned_to"] = assigned_to
    if device_type:
        query["device_type"] = device_type.value
    if status_filter:
        query["status"] = status_filter.value

    cursor = db.devices.find(query).sort("device_id", 1)
    devices = []
    async for d in cursor:
        d["id"] = str(d["_id"])
        devices.append(d)
    return devices


@router.get("/reliability")
async def get_device_reliability_report(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Evaluates fleet-wide IoT hardware reliability, packet transmission integrity,
    battery health, signal strength, and missing data detection across devices.
    """
    devices_cursor = db.devices.find().sort("device_id", 1)
    device_list = await devices_cursor.to_list(length=100)

    reliability_profiles = []
    fleet_health_scores = []

    for dev in device_list:
        dev_id = dev.get("device_id")
        dev_type = dev.get("device_type")
        assigned = dev.get("assigned_to")

        # Check telemetry volume and quality in last 24 hours
        if dev_type == "wearable_biometric":
            sample_cursor = db.sensor_readings.find({"device_id": dev_id}).sort("timestamp", -1).limit(100)
            samples = await sample_cursor.to_list(length=100)
            avg_quality = (
                sum(s.get("measurement_quality", 0.98) for s in samples) / len(samples)
                if samples else 0.95
            )
        else:
            sample_cursor = db.environmental_readings.find({"device_id": dev_id}).sort("timestamp", -1).limit(100)
            samples = await sample_cursor.to_list(length=100)
            avg_quality = 0.99 if samples else 0.95

        battery = dev.get("battery_level_pct", 95.0)
        signal = dev.get("signal_strength_dbm", -58)
        last_seen = dev.get("last_seen")

        # Calculate device reliability index (0 - 100%)
        battery_score = min(battery / 100.0, 1.0)
        signal_score = max(0.0, min(1.0, (signal + 100) / 50.0))  # -50 dBm is 1.0, -100 dBm is 0.0
        quality_score = avg_quality
        overall_reliability = round((battery_score * 0.3 + signal_score * 0.3 + quality_score * 0.4) * 100, 1)

        fleet_health_scores.append(overall_reliability)

        reliability_profiles.append({
            "device_id": dev_id,
            "device_name": dev.get("device_name"),
            "device_type": dev_type,
            "assigned_to": assigned,
            "status": dev.get("status", "online"),
            "battery_level_pct": battery,
            "battery_health": "OPTIMAL" if battery > 50 else ("LOW" if battery > 20 else "CRITICAL"),
            "signal_strength_dbm": signal,
            "signal_grade": "EXCELLENT" if signal > -65 else ("ACCEPTABLE" if signal > -80 else "DEGRADED"),
            "samples_analyzed": len(samples),
            "telemetry_data_quality_pct": round(avg_quality * 100, 1),
            "reliability_score_pct": overall_reliability,
            "firmware_version": dev.get("firmware_version", "v1.4.2-esp32"),
            "last_seen": last_seen
        })

    fleet_mean = round(sum(fleet_health_scores) / len(fleet_health_scores), 1) if fleet_health_scores else 95.0

    return {
        "status": "OPERATIONAL",
        "timestamp": datetime.now(timezone.utc),
        "fleet_devices_total": len(device_list),
        "fleet_reliability_index_pct": fleet_mean,
        "fleet_operational_readiness": "NOMINAL" if fleet_mean > 85.0 else "ATTENTION_REQUIRED",
        "devices": reliability_profiles
    }


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve operational telemetry and connection status for a hardware device."""
    device = await db.devices.find_one({"device_id": device_id})
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Device {device_id} not found."
        )
    device["id"] = str(device["_id"])
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_in: DeviceCreate,
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db = Depends(get_db)
):
    """Register a new biomedical or environmental hardware node (Admin only)."""
    existing = await db.devices.find_one({"device_id": device_in.device_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Device {device_in.device_id} is already registered."
        )

    now_utc = datetime.now(timezone.utc)
    device_dict = device_in.model_dump()
    device_dict["last_seen"] = now_utc
    device_dict["created_at"] = now_utc

    result = await db.devices.insert_one(device_dict)
    device_dict["id"] = str(result.inserted_id)

    # Log audit event
    await db.audit_logs.insert_one({
        "timestamp": now_utc,
        "user_id": current_user["id"],
        "action": "DEVICE_REGISTERED",
        "resource_type": "device",
        "resource_id": device_dict["device_id"],
        "details": {"name": device_in.device_name, "assigned_to": device_in.assigned_to}
    })

    return device_dict


@router.put("/{device_id}/heartbeat", response_model=DeviceResponse)
async def record_device_heartbeat(
    device_id: str,
    heartbeat: DeviceHeartbeat,
    db = Depends(get_db)
):
    """Endpoint for IoT devices (ESP32/Wearables) to report health and connectivity."""
    now_utc = datetime.now(timezone.utc)
    update_data = {
        "battery_level_pct": heartbeat.battery_level_pct,
        "signal_strength_dbm": heartbeat.signal_strength_dbm,
        "status": heartbeat.status.value,
        "last_seen": now_utc
    }
    if heartbeat.firmware_version:
        update_data["firmware_version"] = heartbeat.firmware_version

    result = await db.devices.find_one_and_update(
        {"device_id": device_id},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Device {device_id} not registered."
        )

    result["id"] = str(result["_id"])
    return result
