"""
AstroHealth System Configuration Module
Provides centralized configuration loaded from environment variables.
"""
import os
from pathlib import Path
from typing import List

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AstroHealth")
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Security
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "astrohealth-deep-space-secret-key-super-secure-change-in-prod-9847238472"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",") if origin.strip()
    ]

    # Database (MongoDB Primary + SQLite Offline Local Buffer)
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "astrohealth_db")
    OFFLINE_SQLITE_PATH: str = str(BASE_DIR / os.getenv("OFFLINE_SQLITE_PATH", "astrohealth_offline_buffer.db"))

    # MQTT Hardware Broker
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_KEEP_ALIVE: int = int(os.getenv("MQTT_KEEP_ALIVE", "60"))
    MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "astrohealth/")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "astrohealth_backend_service")

    # Simulation & AI
    SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "True").lower() in ("true", "1", "t")
    SIMULATION_INTERVAL_SECONDS: float = float(os.getenv("SIMULATION_INTERVAL_SECONDS", "2.0"))
    ANOMALY_CONTAMINATION: float = float(os.getenv("ANOMALY_CONTAMINATION", "0.08"))
    SHAP_BACKGROUND_SAMPLES: int = int(os.getenv("SHAP_BACKGROUND_SAMPLES", "50"))
    FORECAST_HORIZON_STEPS: int = int(os.getenv("FORECAST_HORIZON_STEPS", "12"))

settings = Settings()

