"""
AstroHealth Physiological and Environmental Simulation Engine
Generates realistic, time-correlated biometrics and life support telemetry
with 10 selectable mission scenarios, mathematical noise models, and hardware emulation.
"""
import asyncio
import logging
import math
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger("astrohealth.simulator")


class SimulationScenario(str, Enum):
    NORMAL = "normal"                                      # Scenario 1: Nominal astronaut baseline
    ELEVATED_HEART_RATE = "elevated_heart_rate"            # Scenario 2: Resting tachycardia / stress spike
    REDUCED_SLEEP = "reduced_sleep"                        # Scenario 3: Chronic sleep debt & fatigue
    REDUCED_ACTIVITY = "reduced_activity"                  # Scenario 4: Hypokinesia / microgravity deconditioning
    ABNORMAL_SPO2 = "abnormal_spo2"                        # Scenario 5: Hypoxia event (<88% SpO2)
    HIGH_STRESS = "high_stress"                            # Scenario 6: High psychological stress & low HRV
    CO2_SURGE = "co2_surge"                                # Scenario 7: Life-support scrubber degradation (>2000 ppm)
    RADIATION_SPIKE = "radiation_spike"                    # Scenario 8: Solar Particle Event (SPE) (>80 uSv/h)
    SENSOR_DISCONNECTION = "sensor_disconnection"          # Scenario 9: Packet loss / telemetry dropouts
    INVALID_MEASUREMENTS = "invalid_measurements"          # Scenario 10: Artifacts / sensor contact degradation


class SimulationEngine:
    """
    Manages continuous generation and dispatch of simulated telemetry frames.
    Can be started, paused, stopped, and switched dynamically across 10 scenarios.
    """
    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = False
        self.scenario: SimulationScenario = SimulationScenario.NORMAL
        self.interval_seconds: float = 2.0
        self.target_astronaut_id: str = "ASTRO-001"
        self._task: Optional[asyncio.Task] = None
        self.step_count: int = 0
        self.generated_samples_count: int = 0

        # State trackers for smooth time-dependent drift
        self._current_hr: float = 64.0
        self._current_spo2: float = 98.4
        self._current_temp: float = 36.75
        self._current_co2: float = 520.0
        self._current_radiation: float = 21.5
        self._cumulative_rad: float = 43.150

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the simulation engine."""
        return {
            "status": "running" if self.is_running and not self.is_paused else ("paused" if self.is_paused else "stopped"),
            "scenario": self.scenario.value,
            "interval_seconds": self.interval_seconds,
            "target_astronaut_id": self.target_astronaut_id,
            "generated_samples_count": self.generated_samples_count,
            "scenario_descriptions": {
                "normal": "1. Nominal physiological baselines and atmospheric conditions",
                "elevated_heart_rate": "2. Elevated resting heart rate (tachycardia onset)",
                "reduced_sleep": "3. Sleep deprivation and circadian disruption",
                "reduced_activity": "4. Reduced physical movement (hypokinesia)",
                "abnormal_spo2": "5. Acute desaturation and hypoxia drop (< 88% SpO2)",
                "high_stress": "6. Acute psychological stress (suppressed HRV)",
                "co2_surge": "7. Environmental CO2 accumulation (> 2000 ppm)",
                "radiation_spike": "8. Solar radiation event / high cosmic ray flux",
                "sensor_disconnection": "9. Hardware node packet loss and dropouts",
                "invalid_measurements": "10. Sensor detachment and degraded measurement quality"
            }
        }

    def set_scenario(self, scenario_name: str) -> str:
        """Switch active simulation scenario."""
        try:
            self.scenario = SimulationScenario(scenario_name)
            self.step_count = 0
            logger.info(f"Simulation scenario switched to: {self.scenario.value}")
            return self.scenario.value
        except ValueError:
            raise ValueError(f"Invalid scenario '{scenario_name}'. Valid: {[s.value for s in SimulationScenario]}")

    def generate_biometric_frame(self, astronaut_id: str) -> Dict[str, Any]:
        """Generates a mathematically coherent, realistic biometric telemetry reading."""
        self.step_count += 1
        t = self.step_count
        now_utc = datetime.now(timezone.utc)

        # Baseline parameters
        base_hr = 64.0
        base_hrv = 70.0
        base_spo2 = 98.4
        base_temp = 36.75
        motion_mag = random.uniform(0.04, 0.20)
        activity = "rest"
        quality = 0.98

        # Apply scenario-specific physiological dynamics
        if self.scenario == SimulationScenario.NORMAL:
            # Gentle sinus rhythm fluctuation
            hr = base_hr + 3.0 * math.sin(t * 0.15) + random.uniform(-1.5, 1.5)
            hrv = base_hrv + random.uniform(-4.0, 4.0)
            spo2 = min(99.8, base_spo2 + random.uniform(-0.4, 0.4))
            temp = base_temp + 0.1 * math.sin(t * 0.05) + random.uniform(-0.05, 0.05)
            motion_mag = random.uniform(0.05, 0.25)
            activity = "light" if motion_mag > 0.20 else "rest"

        elif self.scenario == SimulationScenario.ELEVATED_HEART_RATE:
            # Steady climb to 125-140 bpm (Resting Tachycardia)
            climb = min(70.0, t * 2.5)
            hr = base_hr + climb + random.uniform(-2.0, 4.0)
            hrv = max(20.0, base_hrv - (climb * 0.6) + random.uniform(-3.0, 3.0))
            spo2 = max(95.0, base_spo2 - 1.2 + random.uniform(-0.5, 0.5))
            temp = base_temp + 0.35 + random.uniform(-0.05, 0.1)
            activity = "rest"  # Elevated while resting triggers alert!

        elif self.scenario == SimulationScenario.REDUCED_SLEEP:
            # Elevated baseline stress, jittery HR, reduced HRV
            hr = base_hr + 12.0 + random.uniform(-3.0, 5.0)
            hrv = max(25.0, base_hrv - 28.0 + random.uniform(-4.0, 4.0))
            spo2 = base_spo2 + random.uniform(-0.8, 0.3)
            temp = base_temp - 0.2 + random.uniform(-0.1, 0.1)
            motion_mag = random.uniform(0.02, 0.10)
            activity = "rest"

        elif self.scenario == SimulationScenario.REDUCED_ACTIVITY:
            # Near-zero acceleration, hypokinesia
            hr = base_hr - 6.0 + random.uniform(-1.0, 1.0)
            hrv = base_hrv + random.uniform(-2.0, 2.0)
            spo2 = base_spo2 + random.uniform(-0.3, 0.3)
            temp = base_temp - 0.15 + random.uniform(-0.05, 0.05)
            motion_mag = random.uniform(0.005, 0.02)
            activity = "rest"

        elif self.scenario == SimulationScenario.ABNORMAL_SPO2:
            # Rapid hypoxic desaturation drop to 84-87%
            drop = min(14.0, t * 0.9)
            spo2 = base_spo2 - drop + random.uniform(-0.6, 0.6)
            hr = base_hr + (drop * 2.2) + random.uniform(-2.0, 2.0)  # Compensatory tachycardia
            hrv = max(22.0, base_hrv - 30.0 + random.uniform(-3.0, 3.0))
            temp = base_temp + random.uniform(-0.1, 0.1)
            activity = "rest"

        elif self.scenario == SimulationScenario.HIGH_STRESS:
            # Sympathetic nervous system overdrive (low HRV, elevated HR)
            hr = base_hr + 28.0 + random.uniform(-4.0, 6.0)
            hrv = max(18.0, 22.0 + random.uniform(-3.0, 3.0))
            spo2 = base_spo2 - 0.6 + random.uniform(-0.4, 0.4)
            temp = base_temp + 0.2 + random.uniform(-0.05, 0.1)
            motion_mag = random.uniform(0.15, 0.40)
            activity = "light"

        elif self.scenario == SimulationScenario.SENSOR_DISCONNECTION:
            # Simulate intermittent packet loss
            if random.random() < 0.60:
                return {}  # Dropped frame to simulate disconnection!
            hr = base_hr + random.uniform(-2.0, 2.0)
            hrv = base_hrv + random.uniform(-3.0, 3.0)
            spo2 = base_spo2
            temp = base_temp

        elif self.scenario == SimulationScenario.INVALID_MEASUREMENTS:
            # Sensor contact degraded or invalid spikes
            quality = round(random.uniform(0.15, 0.45), 2)
            hr = random.choice([25.0, 240.0, base_hr + random.uniform(-20.0, 40.0)])
            spo2 = random.choice([55.0, 100.0, base_spo2 - 8.0])
            hrv = random.uniform(5.0, 150.0)
            temp = random.choice([32.0, 42.0, base_temp])

        else:
            hr = base_hr + random.uniform(-2.0, 2.0)
            hrv = base_hrv + random.uniform(-3.0, 3.0)
            spo2 = base_spo2
            temp = base_temp

        # Acceleration 3-axis vectors
        mx = round(random.uniform(-0.15, 0.15), 3)
        my = round(random.uniform(-0.15, 0.15), 3)
        mz = round(math.sqrt(max(0.01, motion_mag**2 - mx**2 - my**2)), 3)

        return {
            "astronaut_id": astronaut_id,
            "device_id": f"DEV-BIO-{astronaut_id[-3:]}",
            "timestamp": now_utc,
            "heart_rate": round(hr, 1),
            "hrv": round(hrv, 1),
            "spo2": round(min(100.0, max(40.0, spo2)), 1),
            "body_temp": round(temp, 2),
            "temp_measurement_type": "continuous_core_probe",
            "motion_x": mx,
            "motion_y": my,
            "motion_z": mz,
            "motion_magnitude": round(motion_mag, 3),
            "activity_level": activity,
            "measurement_quality": quality,
            "is_simulated": True
        }

    def generate_environmental_frame(self, compartment_id: str = "Command_Module") -> Dict[str, Any]:
        """Generates life support atmospheric and radiation telemetry for a cabin."""
        self.step_count += 1
        now_utc = datetime.now(timezone.utc)
        t = self.step_count

        base_temp = 21.6
        base_humidity = 44.5
        base_pressure = 101.3
        base_co2 = 520.0
        base_rad = 21.8

        co2 = base_co2 + random.uniform(-20.0, 20.0)
        rad_rate = base_rad + random.uniform(-1.0, 1.2)
        temp = base_temp + random.uniform(-0.3, 0.4)
        humidity = base_humidity + random.uniform(-1.5, 1.5)
        pressure = base_pressure + random.uniform(-0.2, 0.2)

        if self.scenario == SimulationScenario.CO2_SURGE:
            # Progressive scrubber saturation climbing to 2400+ ppm
            co2 = min(2800.0, base_co2 + (t * 60.0) + random.uniform(-30.0, 50.0))

        elif self.scenario == SimulationScenario.RADIATION_SPIKE:
            # Solar Particle Event spike climbing to 95-130 uSv/h
            rad_rate = min(140.0, base_rad + (t * 4.5) + random.uniform(-4.0, 8.0))

        # Accumulate cumulative dose (uSv to mSv conversion)
        self._cumulative_rad += (rad_rate * (self.interval_seconds / 3600.0)) / 1000.0

        return {
            "compartment_id": compartment_id,
            "device_id": "DEV-ENV-001" if compartment_id == "Command_Module" else "DEV-ENV-002",
            "timestamp": now_utc,
            "temperature": round(temp, 2),
            "humidity": round(humidity, 1),
            "atmospheric_pressure": round(pressure, 2),
            "co2_ppm": round(co2, 1),
            "voc_index": round(95.0 + random.uniform(-5.0, 8.0), 1),
            "radiation_dose_rate_uSv_h": round(rad_rate, 2),
            "radiation_cumulative_mSv": round(self._cumulative_rad, 4),
            "radiation_exposure_estimated": round(43.1, 2),
            "sensor_status": "NOMINAL" if co2 < 1200.0 and rad_rate < 45.0 else "WARNING",
            "is_simulated": True
        }

    async def _run_loop(self, ingestion_callback):
        """Asynchronous execution loop that feeds simulated readings to backend."""
        logger.info("Simulation loop started.")
        while self.is_running:
            if not self.is_paused:
                try:
                    # Generate frame for target astronaut
                    bio_frame = self.generate_biometric_frame(self.target_astronaut_id)
                    # Generate frame for cabin environment
                    env_frame = self.generate_environmental_frame("Command_Module")

                    if bio_frame:
                        await ingestion_callback("biometric", bio_frame)
                        self.generated_samples_count += 1

                    if env_frame:
                        await ingestion_callback("environmental", env_frame)

                except Exception as e:
                    logger.error(f"Error in simulation loop: {e}")

            await asyncio.sleep(self.interval_seconds)
        logger.info("Simulation loop stopped.")

    def start(self, ingestion_callback):
        """Start the simulation background worker."""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._run_loop(ingestion_callback))
            logger.info("Simulation engine started.")

    def pause(self):
        """Pause frame generation without stopping background worker."""
        self.is_paused = True
        logger.info("Simulation engine paused.")

    def resume(self):
        """Resume paused frame generation."""
        self.is_paused = False
        logger.info("Simulation engine resumed.")

    def stop(self):
        """Stop background simulation worker."""
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Simulation engine stopped.")


# Global singleton simulator instance
simulator_engine = SimulationEngine()
