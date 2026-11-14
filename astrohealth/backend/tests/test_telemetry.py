"""
AstroHealth Phase 2 Test Suite
Tests Astronaut APIs, Mission & Device management, Telemetry Ingestion,
Physiological Range Validations, Safety Rules, and Historical Time-Series Queries.
"""
import pytest
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import DatabaseManager, get_db
from seed import seed_database
from models.schemas import (
    SensorReadingCreate,
    EnvironmentalReadingCreate,
    ActivityLevel,
    TemperatureMeasurementType,
    DeviceHeartbeat,
    DeviceStatus,
    UserRole
)
from routers import astronauts, missions, devices, telemetry

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    seed_database()

@pytest.mark.anyio
async def test_list_and_get_astronauts():
    """Verify listing and retrieving astronaut profiles and baselines."""
    db = await get_db()
    current_user = {"id": "1", "username": "admin", "role": "admin"}
    
    astro_list = await astronauts.list_astronauts(mission_id=None, current_user=current_user, db=db)
    assert len(astro_list) >= 3
    assert any(a["astronaut_id"] == "ASTRO-001" for a in astro_list)

    astro_001 = await astronauts.get_astronaut_profile("ASTRO-001", current_user=current_user, db=db)
    assert astro_001["full_name"] == "Cmdr. Alex Novak"
    assert astro_001["baseline_vitals"]["resting_heart_rate"] == 62.0
    assert "DEV-BIO-001" in astro_001["assigned_devices"]

@pytest.mark.anyio
async def test_mission_endpoints():
    """Verify mission details and habitat compartments."""
    db = await get_db()
    current_user = {"id": "1", "username": "admin", "role": "admin"}

    all_missions = await missions.list_missions(current_user=current_user, db=db)
    assert len(all_missions) >= 1
    
    ares_v = await missions.get_mission("ARES-V", current_user=current_user, db=db)
    assert ares_v["mission_code"] == "ARES-V"
    assert "Command_Module" in ares_v["habitat_compartments"]

@pytest.mark.anyio
async def test_devices_and_heartbeat():
    """Verify device registration status and IoT heartbeat updates."""
    db = await get_db()
    current_user = {"id": "1", "username": "admin", "role": "admin"}

    dev_list = await devices.list_devices(current_user=current_user, db=db)
    assert len(dev_list) >= 5

    # Send heartbeat from DEV-BIO-001
    hb = DeviceHeartbeat(
        battery_level_pct=91.5,
        signal_strength_dbm=-48,
        status=DeviceStatus.ONLINE
    )
    updated_dev = await devices.record_device_heartbeat("DEV-BIO-001", hb, db=db)
    assert updated_dev["battery_level_pct"] == 91.5
    assert updated_dev["status"] == "online"

@pytest.mark.anyio
async def test_biometric_telemetry_ingestion():
    """Verify ingesting a valid biometric reading from wearable bio-band."""
    db = await get_db()
    now_utc = datetime.now(timezone.utc)
    
    reading_in = SensorReadingCreate(
        astronaut_id="ASTRO-001",
        device_id="DEV-BIO-001",
        timestamp=now_utc,
        heart_rate=68.5,
        hrv=70.2,
        spo2=98.8,
        body_temp=36.75,
        temp_measurement_type=TemperatureMeasurementType.CONTINUOUS_CORE_PROBE,
        motion_x=0.04,
        motion_y=0.01,
        motion_z=0.99,
        activity_level=ActivityLevel.REST,
        measurement_quality=0.98,
        is_simulated=True
    )
    res = await telemetry.ingest_biometric_reading(reading_in, db=db)
    assert res["id"] is not None
    assert res["heart_rate"] == 68.5
    assert res["motion_magnitude"] > 0.9

@pytest.mark.anyio
async def test_biometric_range_validation():
    """Verify rejection of non-physiological biometric values (SpO2 > 100 or HR > 280)."""
    from fastapi import HTTPException
    db = await get_db()
    
    # Invalid SpO2 (> 100%)
    invalid_reading = SensorReadingCreate(
        astronaut_id="ASTRO-001",
        device_id="DEV-BIO-001",
        heart_rate=75.0,
        hrv=60.0,
        spo2=108.0,  # Invalid
        body_temp=36.8
    )
    with pytest.raises(HTTPException) as exc_info:
        await telemetry.ingest_biometric_reading(invalid_reading, db=db)
    assert exc_info.value.status_code == 422
    assert "outside valid pulse oximetry range" in exc_info.value.detail

@pytest.mark.anyio
async def test_clinical_safety_rules_alert_trigger():
    """Verify safety engine triggers critical hypoxia alert when SpO2 drops severely."""
    db = await get_db()
    now_utc = datetime.now(timezone.utc)
    
    hypoxia_reading = SensorReadingCreate(
        astronaut_id="ASTRO-003",
        device_id="DEV-BIO-003",
        timestamp=now_utc,
        heart_rate=88.0,
        hrv=45.0,
        spo2=85.5,  # Severe Hypoxia (< 88%)
        body_temp=36.6,
        activity_level=ActivityLevel.REST,
        is_simulated=True
    )
    await telemetry.ingest_biometric_reading(hypoxia_reading, db=db)

    # Check alert was automatically created
    alert = await db.health_alerts.find_one({
        "astronaut_id": "ASTRO-003",
        "category": "emergency",
        "title": "Severe Hypoxia Warning"
    })
    assert alert is not None
    assert alert["vital_value"] == 85.5
    assert alert["status"] == "active"

@pytest.mark.anyio
async def test_get_latest_and_history_biometrics():
    """Verify querying latest biometrics and historical time-series."""
    db = await get_db()
    latest = await telemetry.get_latest_biometrics("ASTRO-001", db=db)
    assert latest["astronaut_id"] == "ASTRO-001"
    assert "heart_rate" in latest

    history = await telemetry.get_biometric_history("ASTRO-001", limit=10, db=db)
    assert len(history) <= 10
    assert len(history) > 0
    # Chronological check (earlier timestamps before later ones)
    assert history[0]["timestamp"] <= history[-1]["timestamp"]

@pytest.mark.anyio
async def test_environmental_telemetry():
    """Verify ingesting and querying environmental readings for life support monitoring."""
    db = await get_db()
    now_utc = datetime.now(timezone.utc)
    
    env_in = EnvironmentalReadingCreate(
        compartment_id="Command_Module",
        device_id="DEV-ENV-001",
        timestamp=now_utc,
        temperature=21.8,
        humidity=45.2,
        atmospheric_pressure=101.4,
        co2_ppm=560.0,
        voc_index=98.0,
        radiation_dose_rate_uSv_h=22.5,
        radiation_cumulative_mSv=43.1,
        radiation_exposure_estimated=43.0,
        sensor_status="NOMINAL",
        is_simulated=True
    )
    res = await telemetry.ingest_environmental_reading(env_in, db=db)
    assert res["id"] is not None
    assert res["co2_ppm"] == 560.0

    latest_env = await telemetry.get_latest_environmental(db=db)
    assert len(latest_env) >= 1
    assert any(e["compartment_id"] == "Command_Module" for e in latest_env)

@pytest.mark.anyio
async def test_telemetry_summary():
    """Verify system-wide telemetry counters."""
    db = await get_db()
    summary = await telemetry.get_telemetry_summary(db=db)
    assert summary["total_biometric_samples"] > 0
    assert summary["total_environmental_samples"] > 0
    assert "connected_hardware_devices" in summary

