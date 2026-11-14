"""
AstroHealth Simulator Control API Router
Provides endpoints to start, pause, resume, stop, and switch scenarios
for the hardware sensor and environmental simulation engine.
"""
import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Ensure simulator directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root / "simulator"))

from engine import simulator_engine, SimulationScenario
from database import DatabaseManager
from routers.telemetry import (
    ingest_biometric_reading, 
    ingest_environmental_reading
)
from models.schemas import SensorReadingCreate, EnvironmentalReadingCreate

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])


class ScenarioChangeRequest(BaseModel):
    scenario: SimulationScenario


class IntervalChangeRequest(BaseModel):
    interval_seconds: float = Field(..., ge=0.2, le=60.0)


class TargetAstronautRequest(BaseModel):
    astronaut_id: str


async def handle_simulation_frame(frame_type: str, data: dict):
    """Callback routed into the standard backend ingestion pipeline."""
    db = DatabaseManager.db
    if db is None:
        db = await DatabaseManager.get_db()

    try:
        if frame_type == "biometric":
            reading_obj = SensorReadingCreate(**data)
            await ingest_biometric_reading(reading_obj, db=db)
        elif frame_type == "environmental":
            env_obj = EnvironmentalReadingCreate(**data)
            await ingest_environmental_reading(env_obj, db=db)
    except Exception as e:
        # Prevent simulator thread crash on transient errors
        pass


@router.get("/status")
async def get_simulation_status():
    """Retrieve current operational status, active scenario, and sample counters."""
    return simulator_engine.get_status()


@router.post("/start")
async def start_simulation():
    """Start automated hardware telemetry generation."""
    if simulator_engine.is_running and not simulator_engine.is_paused:
        return {"status": "already_running", "message": "Simulation is already active."}
    
    simulator_engine.start(handle_simulation_frame)
    return {
        "status": "running", 
        "message": f"Simulation engine started in scenario: {simulator_engine.scenario.value}",
        "scenario": simulator_engine.scenario.value
    }


@router.post("/pause")
async def pause_simulation():
    """Pause telemetry generation without terminating the worker."""
    simulator_engine.pause()
    return {"status": "paused", "message": "Simulation engine paused."}


@router.post("/resume")
async def resume_simulation():
    """Resume paused telemetry generation."""
    simulator_engine.resume()
    return {"status": "running", "message": "Simulation engine resumed."}


@router.post("/stop")
async def stop_simulation():
    """Stop telemetry generation worker."""
    simulator_engine.stop()
    return {"status": "stopped", "message": "Simulation engine stopped."}


@router.post("/scenario")
async def switch_scenario(request: ScenarioChangeRequest):
    """Select from the 10 aerospace physiological and environmental scenarios."""
    try:
        new_scenario = simulator_engine.set_scenario(request.scenario.value)
        return {
            "status": "success",
            "active_scenario": new_scenario,
            "message": f"Switched to scenario: {new_scenario}"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/interval")
async def change_interval(request: IntervalChangeRequest):
    """Adjust sensor sampling frequency in seconds."""
    simulator_engine.interval_seconds = request.interval_seconds
    return {
        "status": "success",
        "interval_seconds": simulator_engine.interval_seconds,
        "message": f"Sampling interval set to {request.interval_seconds}s"
    }


@router.post("/target")
async def change_target_astronaut(request: TargetAstronautRequest):
    """Switch primary telemetry target astronaut (e.g. ASTRO-001, ASTRO-002, ASTRO-003)."""
    simulator_engine.target_astronaut_id = request.astronaut_id
    return {
        "status": "success",
        "target_astronaut_id": simulator_engine.target_astronaut_id,
        "message": f"Target astronaut changed to {request.astronaut_id}"
    }

