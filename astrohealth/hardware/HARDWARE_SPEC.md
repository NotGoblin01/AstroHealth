# AstroHealth Hardware & IoT Communication Specification

## 1. System Overview
The **AstroHealth** hardware ecosystem comprises wearable crew biometric monitors and cabin environmental pods powered by the ESP32 microcontroller architecture. The system supports full dual-mode operation: physical IoT hardware telemetry ingestion and autonomous mathematical hardware simulation.

---

## 2. Sensor Interfacing & Pinout Specifications

| Sensor | Parameter Measured | Communication Interface | Default Address / Pin | Nominal Operational Range |
| :--- | :--- | :--- | :--- | :--- |
| **MAX30102** | Heart Rate & Blood Oxygen (SpO2) | I2C (400 kHz Fast-Mode) | `0x57` | HR: 30-220 bpm, SpO2: 70-100% |
| **MPU6050** | 3-Axis Acceleration & Movement | I2C | `0x68` (AD0=GND) | Accelerometer ±4g, Gyro ±500°/s |
| **DS18B20** | Continuous Core/Skin Body Temp | 1-Wire Digital Bus | GPIO 4 (4.7kΩ pull-up) | -10°C to +85°C (±0.1°C precision) |
| **BME680** | Atmospheric Temp, Humidity, Pressure, VOC | I2C | `0x76` (or `0x77`) | Press: 30-110 kPa, Humidity: 10-90% |
| **SCD41** | Photoacoustic Carbon Dioxide (CO2) | I2C | `0x62` | 400 - 5000 ppm (±40 ppm accuracy) |
| **Radiation Dosimeter** | Active Ionizing Radiation Flux | Hardware Interrupt (Pulse) | GPIO 2 (Active-Low Interrupt) | 0.01 - 500 µSv/h |

### Radiation Dosimeter Integration Note
Because space-grade and commercial dosimeters exhibit varying conversion factors depending on detector surface area and silicon thickness:
- **Pulse-to-Dose Conversion Formula**:
  $$\text{Dose Rate } (\mu\text{Sv/h}) = \frac{\text{Pulses in 60s}}{\text{Calibration Factor } K}$$
  Where standard silicon PIN diode detectors specify $K \approx 120 \text{ pulses/min per } \mu\text{Sv/h}$.
- When connected via UART/I2C (e.g., RadiationWatch Pocket Geiger or Kromek D3S), data is framed using standard NMEA/ASCII strings and parsed into the unified `radiation_dose_rate_uSv_h` field.

---

## 3. Documented MQTT Topic Architecture

AstroHealth utilizes a hierarchical topic structure under the namespace prefix `astrohealth/`:

### A. Crew Biometrics Stream
- **Topic**: `astrohealth/astronaut/{astronaut_id}/biometrics`
- **Example**: `astrohealth/astronaut/ASTRO-001/biometrics`
- **Payload Schema**:
```json
{
  "astronaut_id": "ASTRO-001",
  "device_id": "DEV-BIO-001",
  "timestamp": "2026-11-11T20:30:00Z",
  "heart_rate": 64.2,
  "hrv": 71.5,
  "spo2": 98.4,
  "body_temp": 36.72,
  "temp_measurement_type": "continuous_core_probe",
  "motion_x": 0.04,
  "motion_y": 0.02,
  "motion_z": 0.98,
  "motion_magnitude": 0.982,
  "activity_level": "rest",
  "measurement_quality": 0.98,
  "is_simulated": false
}
```

### B. Cabin Environmental Pod Stream
- **Topic**: `astrohealth/environment/{compartment_id}`
- **Example**: `astrohealth/environment/Command_Module`
- **Payload Schema**:
```json
{
  "compartment_id": "Command_Module",
  "device_id": "DEV-ENV-001",
  "timestamp": "2026-11-11T20:30:00Z",
  "temperature": 21.6,
  "humidity": 44.5,
  "atmospheric_pressure": 101.32,
  "co2_ppm": 524.0,
  "voc_index": 96.0,
  "radiation_dose_rate_uSv_h": 21.8,
  "radiation_cumulative_mSv": 43.15,
  "radiation_exposure_estimated": 43.10,
  "sensor_status": "NOMINAL",
  "is_simulated": false
}
```

### C. Hardware Node Status & Heartbeat
- **Topic**: `astrohealth/device/{device_id}/status`
- **Example**: `astrohealth/device/DEV-BIO-001/status`
- **Payload Schema**:
```json
{
  "device_id": "DEV-BIO-001",
  "status": "online",
  "battery_level_pct": 94.5,
  "signal_strength_dbm": -52,
  "firmware_version": "v1.4.2-esp32"
}
```

### D. Emergency & Health Alerts
- **Topic**: `astrohealth/alerts/{astronaut_id}`
- **Example**: `astrohealth/alerts/ASTRO-001`
- **Payload Schema**:
```json
{
  "astronaut_id": "ASTRO-001",
  "category": "emergency",
  "title": "Severe Hypoxia Warning",
  "message": "Critical SpO2 drop: 85.5%",
  "vital_value": 85.5,
  "threshold_value": 88.0,
  "status": "active"
}
```

---

## 4. Hardware Reliability & Offline Fault Tolerance

1. **Missing Data Detection**:
   The backend monitors the `last_seen` timestamp of registered hardware nodes. If no heartbeat or telemetry packet is received for $> 30$ seconds, the device status transitions to `degraded` and a notification is dispatched.
2. **Local SPIFFS / Flash Buffering**:
   During spaceflight orbital blackouts or RF communication dropouts, the ESP32 node logs formatted telemetry into a circular flash buffer (`/offline_buffer.jsonl`).
3. **Automatic Reconnection & Burst Flush**:
   Upon reconnection to the AstroHealth gateway, the firmware transmits a status heartbeat and drains its offline buffer with rate limiting to avoid socket saturation.

