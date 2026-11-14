"""
AstroHealth Offline Operations & Edge Synchronization Router
Handles local SQLite buffer status, manual sync triggers, and sync audit logs.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root / "hardware"))

from offline_sync import offline_sync_engine
from database import get_db
from models.schemas import (
    SensorReadingCreate,
    EnvironmentalReadingCreate,
    UserRole
)
from auth.security import get_current_user, require_roles

router = APIRouter(prefix="/api/offline", tags=["Offline Synchronization"])


@router.get("/status")
async def get_offline_status():
    """
    Returns statistics on local SQLite edge storage, pending unsynced records,
    and the most recent synchronization timestamp.
    """
    return offline_sync_engine.get_buffer_status()


@router.post("/buffer/biometrics")
async def buffer_biometric_telemetry(
    reading_in: SensorReadingCreate
):
    """
    Directly buffers a biometric reading to local SQLite edge storage.
    Simulates edge node offline operation when primary MongoDB connection is severed.
    """
    row_id = offline_sync_engine.buffer_sensor_reading(reading_in.model_dump())
    return {
        "status": "BUFFERED_LOCALLY",
        "storage": "SQLite",
        "row_id": row_id,
        "astronaut_id": reading_in.astronaut_id
    }


@router.post("/buffer/environmental")
async def buffer_environmental_telemetry(
    reading_in: EnvironmentalReadingCreate
):
    """
    Directly buffers an environmental pod reading to local SQLite edge storage.
    """
    row_id = offline_sync_engine.buffer_environmental_reading(reading_in.model_dump())
    return {
        "status": "BUFFERED_LOCALLY",
        "storage": "SQLite",
        "row_id": row_id,
        "compartment_id": reading_in.compartment_id
    }


@router.post("/sync")
async def trigger_offline_sync(
    current_user: dict = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.MEDICAL_OFFICER])),
    db = Depends(get_db)
):
    """
    Triggers re-synchronization of all buffered local SQLite records into primary MongoDB.
    Performs duplicate prevention and conflict handling.
    """
    result = await offline_sync_engine.synchronize_with_mongodb(db)
    return result


@router.get("/logs")
async def get_sync_audit_logs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve audit history of data synchronizations from MongoDB."""
    cursor = db.device_sync_logs.find().sort("sync_timestamp", -1).limit(limit)
    logs = []
    async for l in cursor:
        l["id"] = str(l["_id"])
        logs.append(l)
    return logs

