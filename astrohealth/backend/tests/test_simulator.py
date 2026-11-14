"""
AstroHealth Phase 3 Test Suite
Tests Sensor Simulation Engine, 10 Mission Scenarios, Telemetry Stream Dynamics,
Simulator Control APIs, and MQTT Bridge Routing.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add backend and simulator directories to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root / "simulator"))
sys.path.insert(0, str(project_root / "hardware"))

from engine import simulator_engine, SimulationScenario
from mqtt_bridge import AstroHealthMQTTBridge
from routers.simulator import (
    get_simulation_status,
    start_simulation,
    pause_simulation,
    resume_simulation,
    stop_simulation,
    switch_scenario,
    change_interval,
    change_target_astronaut,
    ScenarioChangeRequest,
    IntervalChangeRequest,
    TargetAstronautRequest,
    handle_simulation_frame
)
from database import DatabaseManager, get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from seed import seed_database
    seed_database()

@pytest.mark.anyio
async def test_simulator_status_and_scenario_descriptions():
    """Verify simulator status endpoint returns state and 10 scenario descriptions."""
    status = await get_simulation_status()
    assert "status" in status
    assert "scenario" in status
    assert len(status["scenario_descriptions"]) == 10
    assert "normal" in status["scenario_descriptions"]
    assert "abnormal_spo2" in status["scenario_descriptions"]
    assert "radiation_spike" in status["scenario_descriptions"]

@pytest.mark.anyio
async def test_switch_all_10_scenarios():
    """Verify selecting each of the 10 distinct simulation scenarios."""
    scenarios = [
        SimulationScenario.NORMAL,
        SimulationScenario.ELEVATED_HEART_RATE,
        SimulationScenario.REDUCED_SLEEP,
        SimulationScenario.REDUCED_ACTIVITY,
        SimulationScenario.ABNORMAL_SPO2,
        SimulationScenario.HIGH_STRESS,
        SimulationScenario.CO2_SURGE,
        SimulationScenario.RADIATION_SPIKE,
        SimulationScenario.SENSOR_DISCONNECTION,
        SimulationScenario.INVALID_MEASUREMENTS
    ]

    for s in scenarios:
        req = ScenarioChangeRequest(scenario=s)
        res = await switch_scenario(req)
        assert res["status"] == "success"
        assert res["active_scenario"] == s.value
        assert simulator_engine.scenario == s

@pytest.mark.anyio
async def test_biometric_frame_generation_dynamics():
    """Verify mathematical generator outputs scenario-specific physiological values."""
    # Test 1: Normal scenario
    simulator_engine.set_scenario("normal")
    frame = simulator_engine.generate_biometric_frame("ASTRO-001")
    assert 55.0 <= frame["heart_rate"] <= 75.0
    assert 96.0 <= frame["spo2"] <= 100.0
    assert frame["is_simulated"] is True

    # Test 2: Abnormal SpO2 hypoxia event
    simulator_engine.set_scenario("abnormal_spo2")
    # Step forward to trigger hypoxia drop
    for _ in range(12):
        hypoxia_frame = simulator_engine.generate_biometric_frame("ASTRO-001")
    assert hypoxia_frame["spo2"] < 90.0  # Hypoxia reached

    # Test 3: Elevated resting heart rate
    simulator_engine.set_scenario("elevated_heart_rate")
    for _ in range(15):
        tachy_frame = simulator_engine.generate_biometric_frame("ASTRO-001")
    assert tachy_frame["heart_rate"] > 90.0

@pytest.mark.anyio
async def test_environmental_frame_generation_dynamics():
    """Verify life support atmospheric and radiation generator dynamics."""
    # Test 1: CO2 surge
    simulator_engine.set_scenario("co2_surge")
    for _ in range(15):
        co2_frame = simulator_engine.generate_environmental_frame("Command_Module")
    assert co2_frame["co2_ppm"] > 1000.0

    # Test 2: Radiation spike (Solar Particle Event)
    simulator_engine.set_scenario("radiation_spike")
    for _ in range(15):
        rad_frame = simulator_engine.generate_environmental_frame("Command_Module")
    assert rad_frame["radiation_dose_rate_uSv_h"] > 50.0

@pytest.mark.anyio
async def test_simulator_lifecycle_and_controls():
    """Verify starting, pausing, resuming, interval changes, and stopping the simulator."""
    # Set interval
    int_res = await change_interval(IntervalChangeRequest(interval_seconds=1.5))
    assert int_res["interval_seconds"] == 1.5

    # Set target astronaut
    target_res = await change_target_astronaut(TargetAstronautRequest(astronaut_id="ASTRO-002"))
    assert target_res["target_astronaut_id"] == "ASTRO-002"

    # Start
    start_res = await start_simulation()
    assert start_res["status"] in ["running", "already_running"]
    assert simulator_engine.is_running is True

    # Pause
    pause_res = await pause_simulation()
    assert pause_res["status"] == "paused"
    assert simulator_engine.is_paused is True

    # Resume
    resume_res = await resume_simulation()
    assert resume_res["status"] == "running"
    assert simulator_engine.is_paused is False

    # Stop
    stop_res = await stop_simulation()
    assert stop_res["status"] == "stopped"
    assert simulator_engine.is_running is False

@pytest.mark.anyio
async def test_simulation_frame_ingestion_pipeline():
    """Verify generated simulation frames successfully ingest into MongoDB."""
    db = await get_db()
    simulator_engine.set_scenario("normal")
    sample_frame = simulator_engine.generate_biometric_frame("ASTRO-002")
    
    # Send through handle_simulation_frame
    await handle_simulation_frame("biometric", sample_frame)

    # Verify latest record in DB
    latest = await db.sensor_readings.find_one(
        {"astronaut_id": "ASTRO-002"},
        sort=[("timestamp", -1)]
    )
    assert latest is not None
    assert latest["is_simulated"] is True

@pytest.mark.anyio
async def test_mqtt_bridge_message_routing():
    """Verify MQTT bridge parses and routes hardware topics properly."""
    received = []
    bridge = AstroHealthMQTTBridge()
    bridge.message_callback = lambda f_type, payload: received.append((f_type, payload))

    # Simulate biometrics packet reception on topic
    sample_payload = {
        "heart_rate": 65.5,
        "hrv": 69.0,
        "spo2": 98.5,
        "body_temp": 36.7,
        "motion_x": 0.0,
        "motion_y": 0.0,
        "motion_z": 1.0,
        "activity_level": "rest"
    }
    bridge._route_message("astrohealth/astronaut/ASTRO-001/biometrics", sample_payload)
    
    assert len(received) == 1
    assert received[0][0] == "biometric"
    assert received[0][1]["astronaut_id"] == "ASTRO-001"
    assert received[0][1]["heart_rate"] == 65.5

