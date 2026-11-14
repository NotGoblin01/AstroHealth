"""
Unit and Integration Tests for AstroHealth Offline Operation and Synchronization Engine
Tests edge SQLite buffering, idempotent duplicate prevention, conflict handling,
and synchronization into primary MongoDB.
"""
import pytest
from datetime import datetime, timezone
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root / "hardware"))

from database import DatabaseManager, get_db
from models.schemas import (
    UserRole,
    SensorReadingCreate,
    EnvironmentalReadingCreate
)
from offline_sync import offline_sync_engine
from routers import offline


@pytest.fixture(autouse=True)
async def ensure_db():
    await DatabaseManager.connect()


@pytest.mark.anyio
async def test_offline_edge_buffering_in_sqlite():
    # 1. Buffer unique biometric reading in SQLite
    unique_ts = datetime(2026, 3, 22, 14, 30, 0)
    reading = SensorReadingCreate(
        astronaut_id="ASTRO-001",
        device_id="DEV-OFFLINE-001",
        timestamp=unique_ts,
        heart_rate=76.5,
        hrv=68.0,
        spo2=98.1,
        body_temp=36.8,
        activity_level="rest",
        measurement_quality=0.99,
        is_simulated=True
    )

    row_id = offline_sync_engine.buffer_sensor_reading(reading.model_dump())
    assert row_id is not None

    # Check status
    status = offline_sync_engine.get_buffer_status()
    assert status["status"] == "ready"
    assert status["storage_engine"] == "SQLite"
    assert status["pending_sync"]["biometrics"] >= 1

    # 2. Buffer environmental reading in SQLite
    env_reading = EnvironmentalReadingCreate(
        compartment_id="EVA_Airlock",
        device_id="DEV-OFFLINE-ENV-001",
        timestamp=unique_ts,
        temperature=19.4,
        humidity=42.0,
        atmospheric_pressure=98.5,
        co2_ppm=620.0,
        voc_index=110.0,
        radiation_dose_rate_uSv_h=28.0,
        radiation_cumulative_mSv=16.5,
        radiation_exposure_estimated=20.0,
        sensor_status="NOMINAL",
        is_simulated=True
    )
    env_row_id = offline_sync_engine.buffer_environmental_reading(env_reading.model_dump())
    assert env_row_id is not None


@pytest.mark.anyio
async def test_synchronization_to_mongodb_and_duplicate_prevention():
    db = await get_db()

    # 0. Buffer a fresh record for this test
    sync_test_ts = datetime(2026, 3, 23, 11, 0, 0)
    reading = SensorReadingCreate(
        astronaut_id="ASTRO-001",
        device_id="DEV-SYNC-TEST-001",
        timestamp=sync_test_ts,
        heart_rate=78.0,
        hrv=65.0,
        spo2=98.5,
        body_temp=36.7,
        activity_level="rest",
        measurement_quality=0.99,
        is_simulated=True
    )
    offline_sync_engine.buffer_sensor_reading(reading.model_dump())

    # 1. Trigger synchronization
    sync_result = await offline_sync_engine.synchronize_with_mongodb(db)
    assert sync_result["status"] == "SUCCESS"
    assert sync_result["total_synced"] >= 1

    # Verify pending count dropped in SQLite
    status_after = offline_sync_engine.get_buffer_status()
    assert status_after["pending_sync"]["total_pending"] == 0

    # 2. Verify record exists in MongoDB
    synced_bio = await db.sensor_readings.find_one({
        "device_id": "DEV-SYNC-TEST-001"
    })
    assert synced_bio is not None
    assert synced_bio["heart_rate"] == 78.0

    # 3. Test DUPLICATE PREVENTION:
    # Buffer the exact same timestamp/device again into SQLite
    offline_sync_engine.buffer_sensor_reading(reading.model_dump())

    # Count matching MongoDB docs before sync
    count_before = await db.sensor_readings.count_documents({
        "device_id": "DEV-SYNC-TEST-001",
        "timestamp": sync_test_ts
    })

    # Trigger second sync
    await offline_sync_engine.synchronize_with_mongodb(db)

    # Count matching MongoDB docs after sync - MUST BE EQUAL (no duplicate created!)
    count_after = await db.sensor_readings.count_documents({
        "device_id": "DEV-SYNC-TEST-001",
        "timestamp": sync_test_ts
    })
    assert count_before == count_after, "Duplicate record was created instead of being prevented!"


@pytest.mark.anyio
async def test_offline_router_endpoints():
    db = await get_db()

    admin_user = {
        "id": "usr_admin",
        "username": "admin",
        "role": UserRole.ADMINISTRATOR.value,
        "is_active": True
    }

    # Test status endpoint
    status_res = await offline.get_offline_status()
    assert status_res["status"] == "ready"
    assert "pending_sync" in status_res

    # Test sync router endpoint
    sync_res = await offline.trigger_offline_sync(
        current_user=admin_user,
        db=db
    )
    assert sync_res["status"] == "SUCCESS"

    # Test sync logs endpoint
    logs_res = await offline.get_sync_audit_logs(
        limit=10,
        current_user=admin_user,
        db=db
    )
    assert isinstance(logs_res, list)
    assert len(logs_res) >= 1
    assert logs_res[0]["status"] == "SUCCESS"
