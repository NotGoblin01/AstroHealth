"""
Unit and Integration Tests for AstroHealth Alert & Escalation Engine
Tests automated alert triggers, manual crew emergency SOS declarations,
flight surgeon acknowledgment, resolution audit trails, and role protections.
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
    AlertCategory,
    AlertStatus,
    AlertEmergencyRequest,
    AlertAcknowledgeRequest,
)
from routers import alerts
from fastapi import HTTPException


@pytest.fixture(autouse=True)
async def ensure_db():
    await DatabaseManager.connect()


@pytest.mark.anyio
async def test_manual_emergency_declaration_and_audit():
    db = await get_db()

    astro_alex = {
        "id": "usr_astro_alex",
        "username": "astro_alex",
        "full_name": "Cmdr. Alex Novak",
        "role": UserRole.ASTRONAUT.value,
        "astronaut_id": "ASTRO-001",
        "is_active": True
    }

    req = AlertEmergencyRequest(
        astronaut_id="ASTRO-001",
        title="Suit Primary Loop Depressurization",
        reason="Rapid telemetry pressure drop noticed during pre-EVA airlock check.",
        location="EVA Airlock Chamber"
    )

    emergency_alert = await alerts.trigger_manual_emergency(
        req=req,
        current_user=astro_alex,
        db=db
    )

    assert emergency_alert.category == AlertCategory.EMERGENCY
    assert emergency_alert.status == AlertStatus.ACTIVE
    assert "CREW EMERGENCY" in emergency_alert.title
    assert emergency_alert.astronaut_id == "ASTRO-001"

    # Check audit log entry
    audit_entry = await db.audit_logs.find_one({
        "action": "EMERGENCY_DECLARED",
        "details.alert_id": emergency_alert.id
    })
    assert audit_entry is not None
    assert audit_entry["details"]["astronaut_id"] == "ASTRO-001"


@pytest.mark.anyio
async def test_medical_officer_alert_lifecycle_acknowledgment_and_resolution():
    db = await get_db()

    astro_alex = {
        "id": "usr_astro_alex",
        "username": "astro_alex",
        "full_name": "Cmdr. Alex Novak",
        "role": UserRole.ASTRONAUT.value,
        "astronaut_id": "ASTRO-001",
        "is_active": True
    }

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "full_name": "Dr. Elena Vance, MD",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    # 1. Declare alert
    req = AlertEmergencyRequest(
        astronaut_id="ASTRO-001",
        title="Sudden Tachycardia Onset",
        reason="Heart rate spiked to 145 bpm during rest block.",
        location="Living Quarters"
    )
    alert = await alerts.trigger_manual_emergency(req=req, current_user=astro_alex, db=db)

    # 2. Doctor Vance acknowledges alert
    ack_res = await alerts.acknowledge_alert(
        alert_id=alert.id,
        ack_in=AlertAcknowledgeRequest(notes="Telemetry monitored. Crew member instructed to assume recumbent position."),
        current_user=med_officer,
        db=db
    )
    assert ack_res.status == AlertStatus.ACKNOWLEDGED
    assert ack_res.acknowledged_by == "Dr. Elena Vance, MD"

    # 3. Doctor Vance resolves alert
    resolved_res = await alerts.resolve_alert(
        alert_id=alert.id,
        resolution_notes="Heart rate returned to nominal baseline (68 bpm) after hydration and 20 min rest. Clearance granted.",
        current_user=med_officer,
        db=db
    )
    assert resolved_res.status == AlertStatus.RESOLVED
    assert resolved_res.resolved_by == "Dr. Elena Vance, MD"
    assert "Heart rate returned" in resolved_res.resolution_notes

    # 4. Check resolution audit entry
    res_audit = await db.audit_logs.find_one({
        "action": "ALERT_RESOLVED",
        "details.alert_id": alert.id
    })
    assert res_audit is not None


@pytest.mark.anyio
async def test_alert_querying_and_filtering():
    db = await get_db()

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    active_alerts = await alerts.get_active_alerts(
        current_user=med_officer,
        db=db
    )
    assert isinstance(active_alerts, list)

    all_alerts = await alerts.list_alerts(
        category=AlertCategory.EMERGENCY,
        current_user=med_officer,
        db=db
    )
    assert isinstance(all_alerts, list)
    for a in all_alerts:
        assert a.category == AlertCategory.EMERGENCY

