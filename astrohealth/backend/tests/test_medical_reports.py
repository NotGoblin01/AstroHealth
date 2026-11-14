"""
Unit and Integration Tests for AstroHealth Medical Reports
Tests manual report generation, automated synthesis from telemetry and AI,
role-based access restrictions, and CSV/PDF-ready HTML exports.
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
    MedicalReportCreate,
)
from routers import reports
from fastapi import HTTPException


@pytest.fixture(autouse=True)
async def ensure_db():
    await DatabaseManager.connect()


@pytest.mark.anyio
async def test_manual_medical_report_creation_and_retrieval():
    db = await get_db()

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "email": "elena.vance@astrohealth.space",
        "full_name": "Dr. Elena Vance, MD",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    report_in = MedicalReportCreate(
        astronaut_id="ASTRO-001",
        report_type="daily",
        summary="Nominal daily circadian adaptation check for CDR Alex Mercer.",
        clinical_observations="Resting tachycardia noted during simulated exercise cooldown. SpO2 stable at 98.4%.",
        recommendations=["Increase hydration by 500 mL", "Resume nominal cycle ergometer routine"],
        vitals_snapshot={"heart_rate": {"mean": 74.2, "min": 61.0, "max": 132.0, "unit": "bpm"}},
        ai_insights={"anomaly_score": 0.12, "risk_status": "low"}
    )

    created = await reports.create_medical_report(
        report_in=report_in,
        current_user=med_officer,
        db=db
    )

    assert created.id.startswith("REP-")
    assert created.astronaut_id == "ASTRO-001"
    assert created.author_name == "Dr. Elena Vance, MD"
    assert len(created.recommendations) == 2

    # Retrieve report by ID
    retrieved = await reports.get_medical_report(
        report_id=created.id,
        current_user=med_officer,
        db=db
    )
    assert retrieved.id == created.id
    assert retrieved.summary == report_in.summary


@pytest.mark.anyio
async def test_automated_medical_report_generation():
    db = await get_db()

    med_officer = {
        "id": "usr_med_chen",
        "username": "dr_chen",
        "email": "marcus.chen@astrohealth.space",
        "full_name": "Dr. Marcus Chen, PhD",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    # Generate automated 24-hour report for ASTRO-001
    auto_report = await reports.generate_automated_medical_report(
        astronaut_id="ASTRO-001",
        report_type="daily",
        hours=24,
        current_user=med_officer,
        db=db
    )

    assert auto_report.id.startswith("REP-")
    assert auto_report.astronaut_id == "ASTRO-001"
    assert "AstroHealth Automated" in auto_report.summary
    assert "heart_rate" in auto_report.vitals_snapshot
    assert "cardio_trends" in auto_report.ai_insights
    assert len(auto_report.recommendations) > 0


@pytest.mark.anyio
async def test_astronaut_rbac_and_privacy_isolation():
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

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "email": "elena.vance@astrohealth.space",
        "full_name": "Dr. Elena Vance, MD",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    # 1. Alex should see only ASTRO-001 reports when listing
    alex_reports = await reports.list_medical_reports(
        current_user=astro_alex,
        db=db
    )
    for rep in alex_reports:
        assert rep.astronaut_id == "ASTRO-001"

    # 2. If Alex attempts to view a report belonging to ASTRO-002, access should be forbidden (403)
    sarah_report = await reports.create_medical_report(
        report_in=MedicalReportCreate(
            astronaut_id="ASTRO-002",
            report_type="daily",
            summary="Confidential flight surgeon evaluation for Sarah Connor.",
            clinical_observations="All biomarkers nominal.",
            recommendations=["Maintain schedule"],
        ),
        current_user=med_officer,
        db=db
    )

    with pytest.raises(HTTPException) as exc_info:
        await reports.get_medical_report(
            report_id=sarah_report.id,
            current_user=astro_alex,
            db=db
        )
    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_csv_and_pdf_export_generation():
    db = await get_db()

    med_officer = {
        "id": "usr_med_vance",
        "username": "dr_vance",
        "email": "elena.vance@astrohealth.space",
        "full_name": "Dr. Elena Vance, MD",
        "role": UserRole.MEDICAL_OFFICER.value,
        "is_active": True
    }

    # Create a test report
    test_rep = await reports.create_medical_report(
        report_in=MedicalReportCreate(
            astronaut_id="ASTRO-001",
            report_type="incident",
            summary="Incident report regarding acute decompression test.",
            clinical_observations="Mild transient peripheral desaturation.",
            recommendations=["Monitor continuous SpO2 for 12 hours"],
            vitals_snapshot={"spo2": {"mean": 93.5, "min": 89.0, "unit": "%"}}
        ),
        current_user=med_officer,
        db=db
    )

    # 1. Test CSV export
    csv_response = await reports.export_report_csv(
        report_id=test_rep.id,
        current_user=med_officer,
        db=db
    )
    assert csv_response.media_type == "text/csv"
    assert "attachment; filename=" in csv_response.headers.get("content-disposition", "")

    # Read the streaming body
    csv_body = b""
    async for chunk in csv_response.body_iterator:
        csv_body += chunk
    csv_text = csv_body.decode("utf-8")
    assert "ASTROHEALTH CLINICAL MEDICAL REPORT - EXPORT" in csv_text
    assert test_rep.id in csv_text
    assert "ASTRO-001" in csv_text

    # 2. Test PDF/HTML printable export
    pdf_response = await reports.export_report_pdf(
        report_id=test_rep.id,
        current_user=med_officer,
        db=db
    )
    assert pdf_response.media_type == "text/html"
    html_text = pdf_response.body.decode("utf-8")
    assert "<!DOCTYPE html>" in html_text
    assert "AstroHealth Medical Report" in html_text
    assert test_rep.id in html_text
    assert "Cmdr. Alex Novak" in html_text
