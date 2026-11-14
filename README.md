# ASTROHEALTH: AI-Powered Astronaut Health Monitoring System
> **Intelligent Health Monitoring Beyond Earth** &bull; Project Ares-V: Deep Space Mars Transit

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248.svg?logo=mongodb&logoColor=white)](https://mongodb.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E.svg?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-blue.svg)](https://shap.readthedocs.io)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066.svg?logo=eclipsemosquitto&logoColor=white)](https://mosquitto.org)

---

## 1. System Overview

**AstroHealth** is an advanced aerospace medical monitoring platform engineered for deep-space missions where speed-of-light communication latency prohibits reliance on Earth ground control. The platform integrates IoT wearable biosensors, cabin environmental life support systems, real-time machine learning anomaly detection, explainable AI (SHAP), offline edge buffering, and flight-surgeon decision support consoles.

---

## 2. Key Modules & Capabilities

1. **Astronaut Dashboard**:
   - Real-time biometric telemetry: Heart Rate (MAX30102), Pulse Oximetry (SpO2), HRV (rMSSD), Core Body Temperature (DS18B20), and 3-Axis IMU Acceleration (MPU6050).
   - Time-series biometric charts, circadian summaries, and AI-grounded observations.
   - 1-Click Manual Emergency Distress SOS with mission-wide audio-visual escalation.

2. **Flight Surgeon / Medical Officer Console**:
   - Multi-astronaut crew fleet monitoring with live vital status badges.
   - Clinical deep-dive view with baseline comparison.
   - **AI Anomaly & Explainability Inspector**: Isolation Forest anomaly scores accompanied by interactive **SHAP feature attribution bar charts** displaying exact percentage influences for physiological divergence.
   - **Cardiovascular Autonomic Drift Panel**: Calculates autonomic tone ratio (sympathetic dominant vs parasympathetic recovery), trend slopes, and experimental risk indices.
   - **Clinical Medical Reports Archive**: Automated 24-hour report generation, manual drafting, and direct export to **CSV** and **Printable Aerospace Clinical PDF/HTML** documents.

3. **Cabin Life Support & Environmental Suite**:
   - Multi-compartment selector: `Command_Module`, `Living_Quarters`, `Science_Lab`, `EVA_Airlock`.
   - Real-time measurements: Sensirion SCD41 photoacoustic CO2 detection (ppm), BME680 atmospheric pressure (kPa), temperature, humidity, and VOC index.
   - **Active Radiation Dosimetry**: Continuous silicon solid-state detector monitoring with strict distinction between **measured live dose rate (µSv/h)**, **cumulative mission dose (mSv)**, and **estimated GCR projection (mSv/month)**.

4. **Psychological Wellness & Circadian Recovery**:
   - Confidential daily assessments: Mood valence (1-10), perceived stress (1-10), sleep duration (hours), sleep quality (1-10), fatigue level (1-10), and mission workload.
   - Automated non-diagnostic supportive guidance grounded in aerospace circadian hygiene.
   - Strict privacy isolation: Astronaut records remain confidential to the crew member and authorized flight surgeons.

5. **Intelligent Alert & Safety Engine**:
   - 4 Alert tiers: `informational`, `attention_required`, `urgent_assessment`, `emergency`.
   - Independent deterministic safety rules (hypoxia, severe tachycardia, hypothermia, cabin depressurization, CO2 spikes, and high radiation flux) operate in parallel with AI anomaly detection.
   - Medical officer acknowledgment and resolution workflows with mandatory clinical justifications and persistent audit trails in `audit_logs`.

6. **Offline Operation & SQLite Edge Synchronization**:
   - Zero-loss local buffering in SQLite (`astrohealth_offline_buffer.db`) when primary database or communication is severed.
   - Automated or on-demand batch synchronization to primary MongoDB.
   - **Idempotent Duplicate Prevention**: Compound key upsert logic ensures repeated sync attempts never duplicate biometric or environmental time-series records.

7. **Mathematical Sensor Simulation Engine**:
   - 10 flight scenarios generating correlated, time-dependent physiological and atmospheric telemetry:
     1. `normal_baseline`
     2. `elevated_resting_hr`
     3. `reduced_sleep_debt`
     4. `reduced_activity`
     5. `abnormal_hypoxia`
     6. `elevated_stress`
     7. `environmental_co2_spike`
     8. `radiation_exposure_event`
     9. `sensor_disconnection`
     10. `invalid_sensor_noise`
   - Interactive web-based controls: start, pause, resume, stop, interval rate, and target astronaut selector.

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite 5, Tailwind CSS 3, Lucide React, Recharts, Axios.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, Motor (Async MongoDB), PyMongo, WebSockets.
- **Databases**: MongoDB (primary document & time-series storage), SQLite (offline edge buffer).
- **AI / Machine Learning**: Scikit-Learn (Isolation Forest), Random Forest surrogate, SHAP (`TreeExplainer`), SciPy, NumPy, Pandas.
- **Hardware & IoT**: ESP32 C++ firmware (`hardware/esp32_firmware.ino`), FreeRTOS tasks, Eclipse Mosquitto MQTT broker, `paho-mqtt`.
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 4. Quick Start: Native Execution (Windows / Linux)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB Server running on `localhost:27017`

### Step 1: Set Up Backend Virtual Environment
```bash
# Clone or navigate to the project directory
cd astrohealth

# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Seed Database
```bash
# Run the database seeder (initializes Ares-V mission, 6 users, 3 astronauts, devices, and 4 hours of baseline vitals)
python backend/seed.py
```

### Step 3: Launch FastAPI Backend & Simulation Engine
```bash
# Launch backend server on port 8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend automatically starts the hardware simulator engine in the background and listens on `http://localhost:8000`.

### Step 4: Launch Frontend Aerospace Console
```bash
# In a new terminal window:
cd astrohealth/frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 5. Quick Start: Docker Compose Execution

To launch the complete isolated production environment (MongoDB, Mosquitto MQTT Broker, FastAPI Backend, and Nginx Frontend):

```bash
cd astrohealth
docker-compose up --build
```
Access the application:
- **Aerospace Web UI**: `http://localhost:3000`
- **FastAPI Swagger Docs**: `http://localhost:8000/docs`
- **MQTT Broker**: `localhost:1883`
- **Primary Database**: `localhost:27017`

---

## 6. Default User Accounts & Roles

The system includes pre-configured mission accounts for seamless evaluation:

| Role | Username | Password | Full Name | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Astronaut** | `astro_alex` | `AstroPassword123!` | Cmdr. Alex Novak | Mission Commander (`ASTRO-001`) |
| **Astronaut** | `astro_maya` | `AstroPassword123!` | Lt. Maya Lin | Flight Engineer (`ASTRO-002`) |
| **Astronaut** | `astro_david` | `AstroPassword123!` | Dr. David Okafor | Payload Specialist (`ASTRO-003`) |
| **Medical Officer** | `dr_vance` | `DoctorPassword123!` | Dr. Elena Vance, MD | Chief Flight Surgeon |
| **Medical Officer** | `dr_chen` | `DoctorPassword123!` | Dr. Marcus Chen, PhD | Biomedical Officer |
| **Administrator** | `admin` | `AdminPassword123!` | Sarah Stone | Mission Director |

*Tip: Use the role switcher in the top navigation bar to switch between Astronaut, Flight Surgeon, and Administrator views instantly.*

---

## 7. Running the Automated Test Suite

AstroHealth includes a comprehensive test suite covering all 10 architectural phases:

```bash
# Run all backend unit and integration tests
pytest backend/tests -v
```

### Verified Test Breakdown (45/45 Passing):
- `test_auth.py` (8 tests): Health checks, system info, JWT token issuance, bcrypt verification, role-based authorization.
- `test_telemetry.py` (9 tests): Crew profiles, mission manifests, device heartbeats, sensor validation, clinical safety rules, environmental pods.
- `test_simulator.py` (7 tests): All 10 simulation scenarios, lifecycle controls, frame generation, MQTT bridge routing.
- `test_ai_analytics.py` (7 tests): Isolation Forest anomaly detection, SHAP feature attributions, cardiovascular trend slopes, autonomic balance ratio, behavioral sleep debt, statistical forecasting.
- `test_medical_reports.py` (4 tests): Manual report filing, automated 24h report synthesis, privacy isolation, CSV and printable PDF/HTML document exports.
- `test_wellness_and_environment.py` (4 tests): Daily wellness assessments, supportive insight generation, crew privacy boundaries, environmental life support monitoring across all 4 compartments.
- `test_alerts.py` (3 tests): Manual crew distress SOS declarations, flight surgeon acknowledgment, resolution workflows, and audit logs.
- `test_offline_sync.py` (3 tests): Edge SQLite buffering, idempotent duplicate prevention, conflict resolution, and synchronization into MongoDB.

---

## 8. Physical Hardware Setup (Optional)

When deploying on physical hardware, flash the provided firmware sketch:
- **Firmware Path**: `hardware/esp32_firmware.ino`
- **Supported Microcontroller**: ESP32 DevKit v1 / ESP32-S3
- **Wiring & Pinout**: Documented in `hardware/HARDWARE_SPEC.md`
- **Connected Sensors**:
  - `MAX30102` (I2C: SDA 21, SCL 22) - Heart Rate & SpO2
  - `MPU6050` (I2C: SDA 21, SCL 22) - 3-Axis Accelerometer & Gyro
  - `DS18B20` (OneWire: GPIO 4) - Body Core / Skin Temperature
  - `BME680` (I2C: SDA 21, SCL 22) - Ambient Temperature, Humidity, Barometric Pressure, VOC
  - `SCD41` (I2C: SDA 21, SCL 22) - Photoacoustic Carbon Dioxide
  - `Radiation Dosimeter` (Analog ADC / Pulse Counter: GPIO 34) - Ionizing Radiation Flux Rate

---

## 9. Regulatory & Clinical Disclaimer

> **IMPORTANT**: The machine learning models and analytical indicators provided by AstroHealth (including Isolation Forest anomaly scores, cardiovascular trend slopes, autonomic balance ratios, and statistical forecasts) are designed strictly as **experimental situational decision support tools** for aerospace environments. They do **not** constitute certified clinical medical diagnoses. All high-risk alerts incorporate independent deterministic clinical safety rules and manual escalation channels.

---

## 10. License

Developed for Academic and Hackathon Aerospace Research &bull; Open Source under the MIT License.

