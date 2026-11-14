# AstroHealth API & Architecture Reference Manual
**Project Ares-V: Intelligent Health Monitoring Beyond Earth**

---

## 1. System Architecture Overview

AstroHealth provides a dual-tier telemetry ingestion, clinical analytics, and mission life support platform:
- **Primary Telemetry Pipeline**: High-frequency biometric and environmental frames ingested via MQTT (`1883`) or HTTP REST (`/api/telemetry/*`), written to MongoDB with compound time-series indexes, and broadcasted over WebSockets (`/ws/telemetry`).
- **Offline / Edge Tier**: High-speed local buffering in SQLite (`astrohealth_offline_buffer.db`) with zero-loss idempotent batch synchronization and duplicate prevention.
- **Explainable AI Engine**: Real-time Isolation Forest anomaly detection, surrogate Random Forest classification, and TreeSHAP feature attributions calculating percent contributions toward physiological divergence.

```
                      +---------------------------------------+
                      |   Sensors (MAX30102, BME680, SCD41)   |
                      |   or Mathematical Simulator Engine    |
                      +-------------------+-------------------+
                                          |
                      +-------------------v-------------------+
                      |   MQTT Broker (Eclipse Mosquitto)     |
                      |   Topic: astrohealth/#                |
                      +-------------------+-------------------+
                                          |
                      +-------------------v-------------------+
                      |   FastAPI Backend & Ingestion Engine  |
                      |   - Clinical Safety Rules Engine      |
                      |   - Isolation Forest & SHAP Engine    |
                      |   - WebSocket Broadcaster             |
                      +---------+-------------------+---------+
                                |                   |
             +------------------v---+           +---v------------------+
             |  MongoDB Time-Series |           |  Edge SQLite Buffer  |
             |  Primary Database    |           |  Offline Resilience  |
             +----------------------+           +----------------------+
```

---

## 2. Authentication & Authorization (RBAC)

All secured routes require a standard Bearer token (`Authorization: Bearer <jwt_token>`).

| User Role | Description | Capabilities |
| :--- | :--- | :--- |
| `astronaut` | Active Crew Member | View personal telemetry, submit daily wellness, inspect AI observations, trigger emergency SOS. |
| `medical_officer` | Flight Surgeon | Multi-crew dashboard, view SHAP feature attributions, acknowledge/resolve alerts, generate PDF/CSV medical reports. |
| `admin` | Mission Controller | Register hardware devices, configure simulation scenarios, view audit logs, trigger offline sync. |

### Default Credentials
| Username | Password | Full Name | Role |
| :--- | :--- | :--- | :--- |
| `astro_alex` | `AstroPassword123!` | Cmdr. Alex Novak | Astronaut (`ASTRO-001`) |
| `astro_maya` | `AstroPassword123!` | Lt. Maya Lin | Astronaut (`ASTRO-002`) |
| `astro_david` | `AstroPassword123!` | Dr. David Okafor | Astronaut (`ASTRO-003`) |
| `dr_vance` | `DoctorPassword123!` | Dr. Elena Vance, MD | Medical Officer |
| `dr_chen` | `DoctorPassword123!` | Dr. Marcus Chen, PhD | Medical Officer |
| `admin` | `AdminPassword123!` | Mission Director Sarah Stone | Administrator |

---

## 3. REST API Endpoint Reference

### Authentication
- `POST /api/auth/login`: Authenticate with form or JSON credentials. Returns JWT token and user profile.
- `GET /api/auth/me`: Get profile of currently authenticated user.

### Astronauts & Mission
- `GET /api/astronauts`: List all crew members with baseline vitals and assigned hardware devices.
- `GET /api/astronauts/{astronaut_id}`: Detailed medical profile for an astronaut.
- `GET /api/missions`: Mission parameters, orbital target, crew manifest, and habitat compartments.

### Hardware Devices & Telemetry Ingestion
- `GET /api/devices`: List all registered wearable biometrics, environmental pods, and dosimeters.
- `POST /api/devices`: Register a new hardware device.
- `POST /api/devices/{device_id}/heartbeat`: Device telemetry heartbeat with battery and signal metrics.
- `POST /api/telemetry/biometrics`: Ingest live wearable frame (`MAX30102`, `MPU6050`, `DS18B20`).
- `GET /api/telemetry/biometrics/latest/{astronaut_id}`: Latest biometric readings.
- `GET /api/telemetry/biometrics/history/{astronaut_id}?limit=60&minutes=60`: Time-series biometric frames.
- `POST /api/telemetry/environmental`: Ingest habitat pod frame (`BME680`, `SCD41`, Dosimeter).
- `GET /api/telemetry/environmental/latest`: Latest readings across all 4 habitat compartments.
- `GET /api/telemetry/environmental/history/{compartment_id}?limit=60`: Environmental historical time-series.
- `GET /api/telemetry/summary`: High-level mission biometric summary.

### AI Health Analytics & Explainability
- `POST /api/ai/predict`: Run Isolation Forest anomaly detection + SHAP feature attribution on a biometric frame.
- `GET /api/ai/predictions/latest/{astronaut_id}`: Latest anomaly detection result and SHAP weights.
- `GET /api/ai/trends/cardiovascular/{astronaut_id}?hours=24`: Autonomic tone, slopes, and non-diagnostic risk index.
- `GET /api/ai/behavioral/{astronaut_id}?days=7`: Multi-day sleep debt, fatigue index, and strain trends.
- `GET /api/ai/forecast/{astronaut_id}?indicator=heart_rate&horizon_minutes=60`: Statistical trajectory forecast with 95% confidence bounds.

### Medical Reports
- `GET /api/reports`: List clinical reports (filterable by `astronaut_id` and `report_type`).
- `POST /api/reports`: File manual medical evaluation report.
- `POST /api/reports/generate-auto`: 1-click automated synthesis of 24h clinical report using live telemetry and AI insights.
- `GET /api/reports/{id}`: Retrieve report by ID.
- `GET /api/reports/{id}/export/csv`: Export report and telemetry rows as downloadable CSV.
- `GET /api/reports/{id}/export/pdf`: Render printable aerospace clinical health evaluation document.

### Psychological Wellness
- `POST /api/wellness`: Submit daily mood, perceived stress, sleep hours, sleep quality, and journal note.
- `GET /api/wellness/history/{astronaut_id}?days=14`: Private wellness records (privacy-isolated to user and doctors).
- `GET /api/wellness/latest/{astronaut_id}`: Most recent wellness entry with supportive guidance.

### Alerts & Emergency Notification Engine
- `GET /api/alerts`: List alerts with filtering (`category`, `status`, `astronaut_id`).
- `GET /api/alerts/active`: Retrieve unresolved active safety notifications.
- `POST /api/alerts/emergency`: Manually declare crew emergency distress SOS.
- `POST /api/alerts/{id}/acknowledge`: Acknowledge alert with flight surgeon investigation note.
- `POST /api/alerts/{id}/resolve`: Resolve alert with mandatory clinical justification note.

### Offline Resilience & Edge Synchronization
- `GET /api/offline/status`: Local SQLite storage volume and pending record count.
- `POST /api/offline/buffer/biometrics`: Buffer biometric frame to local SQLite edge storage.
- `POST /api/offline/buffer/environmental`: Buffer environmental frame to local SQLite edge storage.
- `POST /api/offline/sync`: Idempotent batch upload of all buffered records to primary MongoDB.
- `GET /api/offline/logs`: Audit trail of synchronization batches.

---

## 4. Real-Time WebSocket Interface

Connect to: `ws://localhost:8000/ws/telemetry`

Payload types:
- `biometric_telemetry`: Emitted on every wearable sensor ingestion.
- `environmental_telemetry`: Emitted on every cabin compartment reading.
- `health_alert`: Emitted when safety thresholds or AI anomalies trigger alerts.
- `emergency_alert`: High-priority broadcast when crew triggers manual distress.

---

## 5. MQTT Topic Structure

Broker: `localhost:1883`

```
astrohealth/
    astronaut/{astronaut_id}/
        biometrics       # Heart rate, SpO2, HRV, Core Temp
        activity         # 3-axis motion, activity classification
    environment/
        {compartment_id} # Temp, humidity, pressure, CO2, VOC, radiation
    device/
        status           # Device heartbeats, battery, RSSI, firmware
```

