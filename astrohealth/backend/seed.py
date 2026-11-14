"""
AstroHealth Database Seeding Script
Initializes primary MongoDB database with Mission Ares-V, Users, Astronauts,
Hardware Devices, Baseline profiles, and sample historical telemetry.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings
from database import DatabaseManager, OfflineSQLiteManager
from auth.security import get_password_hash
from models.schemas import UserRole, DeviceType, DeviceStatus, MissionStatus

def seed_database():
    print("[*] Starting AstroHealth Database Seeding...")
    db = DatabaseManager.get_sync_db()

    # 1. Clean existing seed collections or initialize fresh
    print("[-] Checking database collections...")
    
    # 2. Seed Users
    users_data = [
        {
            "username": "admin",
            "email": "admin@astrohealth.space",
            "hashed_password": get_password_hash("AdminPassword123!"),
            "full_name": "Flight Director Elena Rostova",
            "role": UserRole.ADMINISTRATOR.value,
            "rank": "Mission Director",
            "callsign": "Control-Lead",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "username": "dr_vance",
            "email": "vance@astrohealth.space",
            "hashed_password": get_password_hash("DoctorPassword123!"),
            "full_name": "Dr. Marcus Vance, MD",
            "role": UserRole.MEDICAL_OFFICER.value,
            "rank": "Chief Medical Officer",
            "callsign": "Caduceus-1",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "username": "dr_chen",
            "email": "chen@astrohealth.space",
            "hashed_password": get_password_hash("DoctorPassword123!"),
            "full_name": "Dr. Sarah Chen, PhD",
            "role": UserRole.MEDICAL_OFFICER.value,
            "rank": "Aerospace Biometrician",
            "callsign": "Caduceus-2",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "username": "astro_alex",
            "email": "alex.novak@astrohealth.space",
            "hashed_password": get_password_hash("AstroPassword123!"),
            "full_name": "Cmdr. Alex Novak",
            "role": UserRole.ASTRONAUT.value,
            "rank": "Mission Commander",
            "callsign": "Pioneer-1",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "username": "astro_maya",
            "email": "maya.lin@astrohealth.space",
            "hashed_password": get_password_hash("AstroPassword123!"),
            "full_name": "Lt. Maya Lin",
            "role": UserRole.ASTRONAUT.value,
            "rank": "Flight Engineer",
            "callsign": "Nova-2",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "username": "astro_david",
            "email": "david.okafor@astrohealth.space",
            "hashed_password": get_password_hash("AstroPassword123!"),
            "full_name": "Dr. David Okafor",
            "role": UserRole.ASTRONAUT.value,
            "rank": "Payload Specialist",
            "callsign": "Cosmos-3",
            "mission_id": "ARES-V",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]

    for u in users_data:
        db.users.update_one({"username": u["username"]}, {"$set": u}, upsert=True)
    print(f"[+] Seeded {len(users_data)} users.")

    # Fetch user IDs for references
    alex_user = db.users.find_one({"username": "astro_alex"})
    maya_user = db.users.find_one({"username": "astro_maya"})
    david_user = db.users.find_one({"username": "astro_david"})

    # 3. Seed Mission
    mission_data = {
        "mission_code": "ARES-V",
        "mission_name": "Project Ares-V: Deep Space Mars Transit",
        "target": "Mars Orbital Insertion & Surface Habitat",
        "launch_date": datetime(2026, 3, 15, 10, 0, 0),
        "planned_duration_days": 580,
        "commanding_officer": "Cmdr. Alex Novak",
        "assigned_crew": ["ASTRO-001", "ASTRO-002", "ASTRO-003"],
        "status": MissionStatus.DEEP_SPACE_TRANSIT.value,
        "habitat_compartments": ["Command_Module", "Living_Quarters", "Science_Lab", "EVA_Airlock"],
        "created_at": datetime.utcnow()
    }
    db.missions.update_one({"mission_code": mission_data["mission_code"]}, {"$set": mission_data}, upsert=True)
    print(f"[+] Seeded Mission: {mission_data['mission_name']}")

    # 4. Seed Astronaut Profiles
    astronauts_data = [
        {
            "astronaut_id": "ASTRO-001",
            "user_id": str(alex_user["_id"]) if alex_user else None,
            "full_name": "Cmdr. Alex Novak",
            "mission_id": "ARES-V",
            "age": 41,
            "sex": "M",
            "blood_type": "O+",
            "role_description": "Commander & Navigation Specialist",
            "assigned_devices": ["DEV-BIO-001", "DEV-DOS-001"],
            "baseline_vitals": {
                "resting_heart_rate": 62.0,
                "resting_hrv": 72.0,
                "baseline_spo2": 98.4,
                "baseline_body_temp": 36.7,
                "resting_systolic_bp": 116.0,
                "resting_diastolic_bp": 74.0
            },
            "medical_clearance_status": "FIT_FOR_MISSION",
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "astronaut_id": "ASTRO-002",
            "user_id": str(maya_user["_id"]) if maya_user else None,
            "full_name": "Lt. Maya Lin",
            "mission_id": "ARES-V",
            "age": 34,
            "sex": "F",
            "blood_type": "A+",
            "role_description": "Flight Engineer & Life Support Systems",
            "assigned_devices": ["DEV-BIO-002", "DEV-DOS-002"],
            "baseline_vitals": {
                "resting_heart_rate": 66.0,
                "resting_hrv": 65.0,
                "baseline_spo2": 98.6,
                "baseline_body_temp": 36.8,
                "resting_systolic_bp": 112.0,
                "resting_diastolic_bp": 72.0
            },
            "medical_clearance_status": "FIT_FOR_MISSION",
            "active": True,
            "created_at": datetime.utcnow()
        },
        {
            "astronaut_id": "ASTRO-003",
            "user_id": str(david_user["_id"]) if david_user else None,
            "full_name": "Dr. David Okafor",
            "mission_id": "ARES-V",
            "age": 39,
            "sex": "M",
            "blood_type": "B+",
            "role_description": "Payload Specialist & Astrobiologist",
            "assigned_devices": ["DEV-BIO-003", "DEV-DOS-003"],
            "baseline_vitals": {
                "resting_heart_rate": 58.0,
                "resting_hrv": 78.0,
                "baseline_spo2": 98.1,
                "baseline_body_temp": 36.6,
                "resting_systolic_bp": 120.0,
                "resting_diastolic_bp": 76.0
            },
            "medical_clearance_status": "FIT_FOR_MISSION",
            "active": True,
            "created_at": datetime.utcnow()
        }
    ]

    for a in astronauts_data:
        db.astronauts.update_one({"astronaut_id": a["astronaut_id"]}, {"$set": a}, upsert=True)
    print(f"[+] Seeded {len(astronauts_data)} astronaut profiles.")

    # 5. Seed Hardware Devices
    devices_data = [
        {
            "device_id": "DEV-BIO-001",
            "device_name": "BioBand Mk-IV (Novak)",
            "device_type": DeviceType.WEARABLE_BIOMETRIC.value,
            "assigned_to": "ASTRO-001",
            "firmware_version": "v1.4.2-esp32",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 94.0,
            "signal_strength_dbm": -52,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "device_id": "DEV-BIO-002",
            "device_name": "BioBand Mk-IV (Lin)",
            "device_type": DeviceType.WEARABLE_BIOMETRIC.value,
            "assigned_to": "ASTRO-002",
            "firmware_version": "v1.4.2-esp32",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 98.0,
            "signal_strength_dbm": -55,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "device_id": "DEV-BIO-003",
            "device_name": "BioBand Mk-IV (Okafor)",
            "device_type": DeviceType.WEARABLE_BIOMETRIC.value,
            "assigned_to": "ASTRO-003",
            "firmware_version": "v1.4.2-esp32",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 89.0,
            "signal_strength_dbm": -61,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "device_id": "DEV-ENV-001",
            "device_name": "Cabin Atmospheric Pod Alpha",
            "device_type": DeviceType.ENVIRONMENTAL_CABIN.value,
            "assigned_to": "Command_Module",
            "firmware_version": "v2.1.0-esp32",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 100.0,
            "signal_strength_dbm": -42,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "device_id": "DEV-ENV-002",
            "device_name": "Cabin Atmospheric Pod Beta",
            "device_type": DeviceType.ENVIRONMENTAL_CABIN.value,
            "assigned_to": "Living_Quarters",
            "firmware_version": "v2.1.0-esp32",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 100.0,
            "signal_strength_dbm": -46,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        },
        {
            "device_id": "DEV-DOS-001",
            "device_name": "Active Silicon Dosimeter 01",
            "device_type": DeviceType.RADIATION_DOSIMETER.value,
            "assigned_to": "ASTRO-001",
            "firmware_version": "v1.1.0-dos",
            "status": DeviceStatus.ONLINE.value,
            "battery_level_pct": 91.0,
            "signal_strength_dbm": -58,
            "last_seen": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
    ]

    for d in devices_data:
        db.devices.update_one({"device_id": d["device_id"]}, {"$set": d}, upsert=True)
    print(f"[+] Seeded {len(devices_data)} IoT hardware devices.")

    # 6. Seed Historical Biometrics (Last 4 hours of readings per astronaut)
    now = datetime.utcnow()
    total_telemetry = 0
    
    for astro in astronauts_data:
        astro_id = astro["astronaut_id"]
        base_hr = astro["baseline_vitals"]["resting_heart_rate"]
        base_hrv = astro["baseline_vitals"]["resting_hrv"]
        base_spo2 = astro["baseline_vitals"]["baseline_spo2"]
        base_temp = astro["baseline_vitals"]["baseline_body_temp"]

        # Only insert if no recent records exist
        existing_count = db.sensor_readings.count_documents({"astronaut_id": astro_id})
        if existing_count < 30:
            readings = []
            for i in range(60, -1, -1):
                timestamp = now - timedelta(minutes=i*2)
                # Realistic biometric micro-fluctuations
                hr = base_hr + random.uniform(-4.0, 7.0)
                hrv = base_hrv + random.uniform(-6.0, 6.0)
                spo2 = min(99.9, base_spo2 + random.uniform(-0.8, 0.6))
                temp = base_temp + random.uniform(-0.2, 0.3)
                motion_mag = random.uniform(0.02, 0.45)
                
                readings.append({
                    "astronaut_id": astro_id,
                    "device_id": f"DEV-BIO-{astro_id[-3:]}",
                    "timestamp": timestamp,
                    "heart_rate": round(hr, 1),
                    "hrv": round(hrv, 1),
                    "spo2": round(spo2, 1),
                    "body_temp": round(temp, 2),
                    "temp_measurement_type": "continuous_core_probe",
                    "motion_x": round(random.uniform(-0.2, 0.2), 3),
                    "motion_y": round(random.uniform(-0.2, 0.2), 3),
                    "motion_z": round(random.uniform(0.9, 1.05), 3),
                    "motion_magnitude": round(motion_mag, 3),
                    "activity_level": "light" if motion_mag > 0.25 else "rest",
                    "measurement_quality": round(random.uniform(0.95, 0.99), 2),
                    "is_simulated": True
                })
            if readings:
                db.sensor_readings.insert_many(readings)
                total_telemetry += len(readings)

    # 7. Seed Environmental Telemetry
    env_count = db.environmental_readings.count_documents({})
    if env_count < 30:
        env_readings = []
        for i in range(60, -1, -1):
            timestamp = now - timedelta(minutes=i*2)
            env_readings.append({
                "compartment_id": "Command_Module",
                "device_id": "DEV-ENV-001",
                "timestamp": timestamp,
                "temperature": round(21.5 + random.uniform(-0.6, 0.8), 2),
                "humidity": round(44.0 + random.uniform(-2.0, 2.5), 1),
                "atmospheric_pressure": round(101.3 + random.uniform(-0.4, 0.4), 2),
                "co2_ppm": round(520.0 + random.uniform(-30.0, 50.0), 1),
                "voc_index": round(95.0 + random.uniform(-5.0, 10.0), 1),
                "radiation_dose_rate_uSv_h": round(21.4 + random.uniform(-1.5, 2.0), 2),
                "radiation_cumulative_mSv": round(42.8 + (60-i)*0.0007, 3),
                "radiation_exposure_estimated": round(42.5, 2),
                "sensor_status": "NOMINAL",
                "is_simulated": True
            })
        if env_readings:
            db.environmental_readings.insert_many(env_readings)

    # 8. Seed Psychological Wellness Record
    wellness_count = db.mental_health_logs.count_documents({})
    if wellness_count == 0:
        db.mental_health_logs.insert_many([
            {
                "astronaut_id": "ASTRO-001",
                "date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                "mood_score": 8,
                "stress_score": 4,
                "sleep_hours": 7.5,
                "sleep_quality_score": 8,
                "fatigue_score": 3,
                "workload_rating": 6,
                "journal_notes": "Nominal mission operations. Completed routine exercise countermeasure.",
                "supportive_insight": "Sleep duration and HRV recovery balance within optimal mission parameters.",
                "created_at": now - timedelta(days=1)
            },
            {
                "astronaut_id": "ASTRO-002",
                "date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                "mood_score": 7,
                "stress_score": 5,
                "sleep_hours": 6.8,
                "sleep_quality_score": 7,
                "fatigue_score": 4,
                "workload_rating": 7,
                "journal_notes": "Life support calibration completed. Slight vestibular adaptation fatigue.",
                "supportive_insight": "Mild workload strain noted; scheduled relaxation period recommended.",
                "created_at": now - timedelta(days=1)
            }
        ])

    # 9. Seed Initial Nominal Alert
    alert_count = db.health_alerts.count_documents({})
    if alert_count == 0:
        db.health_alerts.insert_one({
            "astronaut_id": "ASTRO-002",
            "source": "environmental",
            "category": "informational",
            "title": "Cabin Humidity Nominal Reset",
            "message": "Living Quarters humidity stabilized to 44.5% after life support cycle.",
            "details": {"compartment": "Living_Quarters", "target_humidity": 45.0},
            "status": "resolved",
            "created_at": now - timedelta(hours=3),
            "resolved_at": now - timedelta(hours=2),
            "resolved_by": "System Autonomous Loop"
        })

    # 10. Initialize Offline SQLite schema
    OfflineSQLiteManager.init_offline_db()

    print("[SUCCESS] AstroHealth database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
