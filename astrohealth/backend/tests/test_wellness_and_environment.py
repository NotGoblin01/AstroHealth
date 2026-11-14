"""
Unit and Integration Tests for AstroHealth Psychological Wellness & Cabin Environmental Life Support
Tests daily wellness submissions, privacy boundaries, supportive insight generation,
and environmental telemetry monitoring across habitat compartments.
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root / "ai_engine"))

from database import DatabaseManager, get_db
from models.schemas import (
    UserRole,
    DailyWellnessCreate,
    EnvironmentalReadingCreate
)
from routers import wellness, telemetry
from fastapi import HTTPException


@pytest.fixture(autouse=True)
async def ensure_db():
    await DatabaseManager.connect()


@pytest.mark.anyio
async def test_daily_wellness_submission_and_supportive_insight():
    db = await get_db()

    astro_alex = {
        "id": "usr_astro_alex",
        "username": "astro_alex",
        "email": "alex.mercer@astrohealth.space",
        "full_name": "CDR Alex Mercer",
        "role": UserRole.ASTRONAUT.value,
        "astronaut_id": "ASTRO-001",
        "is_active": True
    }

    # Alex submits wellness with low sleep and high stress
    entry_in = DailyWellnessCreate(
        astronaut_id="ASTRO-001",
        date="2026-03-20",
        mood_score=6,
        stress_score=8,
        sleep_hours=5.2,
        sleep_quality_score=5,
        fatigue_score=8,
        workload_rating=8,
        journal_notes="Simulated orbital insertion burn prep resulted in truncated sleep cycle."
    )

    result = await wellness.submit_daily_wellness(
        entry_in=entry_in,
        current_user=astro_alex,
        db=db
    )

    assert result.astronaut_id == "ASTRO-001"
    assert result.date == "2026-03-20"
    assert result.supportive_insight is not None
    # Insight should mention sleep banking or autonomic wind-down
    assert "sleep banking" in result.supportive_insight.lower() or "sleep duration" in result.supportive_insight.lower()
    assert "stress" in result.supportive_insight.lower() or "fatigue" in result.supportive_insight.lower()


@pytest.mark.anyio
async def test_wellness_privacy_isolation_between_crew():
    db = await get_db()

    astro_alex = {
        "id": "usr_astro_alex",
        "username": "astro_alex",
        "role": UserRole.ASTRONAUT.value,
        "astronaut_id": "ASTRO-001",
        "is_active": True
    }

    astro_sarah = {
        "id": "usr_astro_sarah",
        "username": "astro_sarah",
        "role": UserRole.ASTRONAUT.value,
        "astronaut_id": "ASTRO-002",
        "is_active": True
    }

    # 1. Sarah cannot forge a wellness submission for Alex
    forged_entry = DailyWellnessCreate(
        astronaut_id="ASTRO-001",
        date="2026-03-21",
        mood_score=9,
        stress_score=2,
        sleep_hours=8.0,
        sleep_quality_score=9,
        fatigue_score=2,
        workload_rating=4
    )

    with pytest.raises(HTTPException) as exc_info:
        await wellness.submit_daily_wellness(
            entry_in=forged_entry,
            current_user=astro_sarah,
            db=db
        )
    assert exc_info.value.status_code == 403

    # 2. Sarah cannot read Alex's confidential wellness history
    with pytest.raises(HTTPException) as exc_read:
        await wellness.get_wellness_history(
            astronaut_id="ASTRO-001",
            days=7,
            current_user=astro_sarah,
            db=db
        )
    assert exc_read.value.status_code == 403


@pytest.mark.anyio
async def test_medical_officer_authorized_wellness_access():
    db = await get_db()

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "role": UserRole.MEDICAL_OFFICER.value,
        "full_name": "Dr. Elena Vance, MD",
        "is_active": True
    }

    # Doctor Vance can view Alex's wellness history
    history = await wellness.get_wellness_history(
        astronaut_id="ASTRO-001",
        days=14,
        current_user=med_officer,
        db=db
    )
    assert isinstance(history, list)
    assert len(history) >= 1
    assert history[0].astronaut_id == "ASTRO-001"


@pytest.mark.anyio
async def test_environmental_compartment_telemetry_and_radiation():
    db = await get_db()

    # Ingest test environmental reading for Command Module
    env_reading = EnvironmentalReadingCreate(
        compartment_id="Command_Module",
        device_id="DEV-ENV-001",
        temperature=21.8,
        humidity=48.2,
        atmospheric_pressure=101.3,
        co2_ppm=540.0,
        voc_index=95.0,
        radiation_dose_rate_uSv_h=22.4,
        radiation_cumulative_mSv=14.8,
        radiation_exposure_estimated=18.5,
        sensor_status="NOMINAL",
        is_simulated=False
    )

    ingested = await telemetry.ingest_environmental_reading(env_reading, db=db)
    assert ingested["compartment_id"] == "Command_Module"
    assert ingested["co2_ppm"] == 540.0
    assert ingested["radiation_dose_rate_uSv_h"] == 22.4
    # Clearly verify measured vs estimated radiation distinction
    assert ingested["radiation_cumulative_mSv"] != ingested["radiation_exposure_estimated"]

    # Query latest environmental readings across all compartments
    latest_all = await telemetry.get_latest_environmental(db=db)
    assert len(latest_all) > 0
    compartments = [r["compartment_id"] for r in latest_all]
    assert "Command_Module" in compartments
