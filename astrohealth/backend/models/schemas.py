"""
AstroHealth Data Schemas and Validation Models
Standardized Pydantic models for authentication, users, astronauts,
hardware devices, telemetry, environmental monitoring, AI predictions, and alerts.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# User & Authentication Schemas
# -------------------------------------------------------------
class UserRole(str, Enum):
    ASTRONAUT = "astronaut"
    MEDICAL_OFFICER = "medical_officer"
    ADMINISTRATOR = "admin"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str
    role: UserRole
    callsign: Optional[str] = None
    rank: Optional[str] = None
    mission_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    role: str
    username: str
    exp: Optional[int] = None


# -------------------------------------------------------------
# Astronaut Profile Schemas
# -------------------------------------------------------------
class BaselineVitals(BaseModel):
    resting_heart_rate: float = 65.0
    resting_hrv: float = 68.0
    baseline_spo2: float = 98.2
    baseline_body_temp: float = 36.8
    resting_systolic_bp: float = 118.0
    resting_diastolic_bp: float = 76.0


class AstronautBase(BaseModel):
    astronaut_id: str
    full_name: str
    user_id: Optional[str] = None
    mission_id: str
    age: int
    sex: str
    blood_type: str
    role_description: str
    assigned_devices: List[str] = []
    baseline_vitals: BaselineVitals = Field(default_factory=BaselineVitals)
    medical_clearance_status: str = "FIT_FOR_MISSION"
    active: bool = True


class AstronautCreate(AstronautBase):
    pass


class AstronautResponse(AstronautBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# -------------------------------------------------------------
# Mission Schemas
# -------------------------------------------------------------
class MissionStatus(str, Enum):
    PRE_LAUNCH = "pre_launch"
    ACTIVE = "active"
    ORBITAL = "orbital"
    DEEP_SPACE_TRANSIT = "deep_space_transit"
    SURFACE_OPERATIONS = "surface_operations"
    COMPLETED = "completed"


class MissionBase(BaseModel):
    mission_code: str
    mission_name: str
    target: str
    launch_date: datetime
    planned_duration_days: int
    commanding_officer: str
    assigned_crew: List[str] = []
    status: MissionStatus = MissionStatus.ACTIVE
    habitat_compartments: List[str] = ["Command_Module", "Living_Quarters", "Science_Lab", "EVA_Airlock"]


class MissionCreate(MissionBase):
    pass


class MissionResponse(MissionBase):
    id: str
    created_at: datetime


# -------------------------------------------------------------
# Hardware & Device Schemas
# -------------------------------------------------------------
class DeviceType(str, Enum):
    WEARABLE_BIOMETRIC = "wearable_biometric"  # MAX30102 + MPU6050 + DS18B20
    ENVIRONMENTAL_CABIN = "environmental_cabin"  # BME680 + SCD41
    RADIATION_DOSIMETER = "radiation_dosimeter"  # Active solid-state dosimeter


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class DeviceBase(BaseModel):
    device_id: str
    device_name: str
    device_type: DeviceType
    assigned_to: str  # astronaut_id or compartment_name
    firmware_version: str = "v1.4.2-esp32"
    status: DeviceStatus = DeviceStatus.ONLINE
    battery_level_pct: float = 95.0
    signal_strength_dbm: int = -58
    last_seen: Optional[datetime] = None


class DeviceCreate(DeviceBase):
    auth_token: Optional[str] = None


class DeviceHeartbeat(BaseModel):
    battery_level_pct: float
    signal_strength_dbm: int
    firmware_version: Optional[str] = None
    status: DeviceStatus = DeviceStatus.ONLINE


class DeviceResponse(DeviceBase):
    id: str
    created_at: datetime


# -------------------------------------------------------------
# Telemetry: Sensor Readings (Biometrics)
# -------------------------------------------------------------
class ActivityLevel(str, Enum):
    REST = "rest"
    LIGHT = "light"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    EVA = "eva"


class TemperatureMeasurementType(str, Enum):
    INFRARED_TYMPANIC = "infrared_tympanic"
    CONTINUOUS_CORE_PROBE = "continuous_core_probe"
    EPIDERMAL_PATCH = "epidermal_patch"


class SensorReadingCreate(BaseModel):
    astronaut_id: str
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    heart_rate: float
    hrv: float
    spo2: float
    body_temp: float
    temp_measurement_type: TemperatureMeasurementType = TemperatureMeasurementType.EPIDERMAL_PATCH
    motion_x: float = 0.0
    motion_y: float = 0.0
    motion_z: float = 0.0
    motion_magnitude: float = 0.0
    activity_level: ActivityLevel = ActivityLevel.REST
    measurement_quality: float = Field(default=0.98, ge=0.0, le=1.0)
    is_simulated: bool = False


class SensorReadingResponse(SensorReadingCreate):
    id: str


# -------------------------------------------------------------
# Telemetry: Environmental Readings
# -------------------------------------------------------------
class EnvironmentalReadingCreate(BaseModel):
    compartment_id: str
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float  # Celsius
    humidity: float  # %RH
    atmospheric_pressure: float  # kPa
    co2_ppm: float  # ppm from SCD41
    voc_index: float = 100.0  # BME680 VOC index
    radiation_dose_rate_uSv_h: float  # Measured dose rate uSv/h
    radiation_cumulative_mSv: float  # Accumulated mission dose mSv
    radiation_exposure_estimated: float  # Estimated galactic cosmic ray projection
    sensor_status: str = "NOMINAL"
    is_simulated: bool = False


class EnvironmentalReadingResponse(EnvironmentalReadingCreate):
    id: str


# -------------------------------------------------------------
# Psychological Wellness & Behavioral Health
# -------------------------------------------------------------
class DailyWellnessCreate(BaseModel):
    astronaut_id: str
    date: str  # YYYY-MM-DD
    mood_score: int = Field(..., ge=1, le=10)
    stress_score: int = Field(..., ge=1, le=10)
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    sleep_quality_score: int = Field(..., ge=1, le=10)
    fatigue_score: int = Field(..., ge=1, le=10)
    workload_rating: int = Field(default=5, ge=1, le=10)
    journal_notes: Optional[str] = None


class DailyWellnessResponse(DailyWellnessCreate):
    id: str
    created_at: datetime
    supportive_insight: Optional[str] = None


# -------------------------------------------------------------
# Health Alerts & Safety Notifications
# -------------------------------------------------------------
class AlertCategory(str, Enum):
    INFORMATIONAL = "informational"
    ATTENTION_REQUIRED = "attention_required"
    URGENT_ASSESSMENT = "urgent_assessment"
    EMERGENCY = "emergency"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class HealthAlertCreate(BaseModel):
    astronaut_id: str
    source: str  # biometric, environmental, ai_model, manual_emergency
    category: AlertCategory
    title: str
    message: str
    details: Dict[str, Any] = {}
    vital_value: Optional[float] = None
    threshold_value: Optional[float] = None
    status: AlertStatus = AlertStatus.ACTIVE


class HealthAlertResponse(HealthAlertCreate):
    id: str
    created_at: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class AlertEmergencyRequest(BaseModel):
    astronaut_id: str
    title: str
    reason: str
    location: Optional[str] = "Crew Compartment Alpha"


# -------------------------------------------------------------
# AI Predictions & Explainability
# -------------------------------------------------------------
class AnomalyFeatureContribution(BaseModel):
    feature_name: str
    feature_value: float
    shap_value: float
    contribution_direction: str  # higher_risk, lower_risk
    baseline_value: float


class AIPredictionResponse(BaseModel):
    id: str
    astronaut_id: str
    timestamp: datetime
    model_name: str
    is_anomaly: bool
    anomaly_score: float  # -1.0 to 1.0 (Isolation Forest score)
    confidence: float
    data_quality_score: float
    contributing_features: List[AnomalyFeatureContribution] = []
    clinical_observation: str
    model_version: str = "astrohealth-isoforest-v1.2"
    experimental_disclaimer: str = (
        "Experimental aerospace health analytics indicator. "
        "Not a substitute for certified clinical diagnosis."
    )


# -------------------------------------------------------------
# Medical Reports
# -------------------------------------------------------------
class MedicalReportCreate(BaseModel):
    astronaut_id: str
    report_type: str = "daily"  # daily, weekly, incident, clearance
    summary: str
    clinical_observations: str
    recommendations: List[str]
    vitals_snapshot: Dict[str, Any] = {}
    ai_insights: Dict[str, Any] = {}


class MedicalReportResponse(MedicalReportCreate):
    id: str
    author_id: str
    author_name: str
    created_at: datetime


# -------------------------------------------------------------
# Offline Sync Schemas
# -------------------------------------------------------------
class OfflineSyncBatchRequest(BaseModel):
    device_id: str
    astronaut_readings: List[SensorReadingCreate] = []
    environmental_readings: List[EnvironmentalReadingCreate] = []


class OfflineSyncBatchResponse(BaseModel):
    status: str
    synced_astronaut_readings: int
    synced_environmental_readings: int
    server_time: datetime
