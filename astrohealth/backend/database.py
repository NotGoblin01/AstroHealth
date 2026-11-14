"""
AstroHealth Database Management Module
Implements MongoDB connection with Motor (Async) and PyMongo (Sync),
along with offline SQLite local storage buffering.
"""
import logging
import sqlite3
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from pymongo import MongoClient

from config import settings

logger = logging.getLogger("astrohealth.database")

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    sync_client: Optional[MongoClient] = None
    _loop = None

    @classmethod
    async def connect(cls):
        """Establish asynchronous connection to MongoDB and ensure indexes."""
        import asyncio
        try:
            current_loop = asyncio.get_running_loop()
            if cls.client is None or cls._loop is not current_loop:
                logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")
                cls.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
                cls.db = cls.client[settings.MONGODB_DATABASE]
                cls._loop = current_loop
                # Test connection ping
                await cls.client.admin.command('ping')
                logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DATABASE}")
                await cls.create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}. Switching to degraded/offline mode capability.")

    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_sync_db(cls):
        """Returns a synchronous PyMongo database connection for scripts/seed."""
        if cls.sync_client is None:
            cls.sync_client = MongoClient(settings.MONGODB_URI)
        return cls.sync_client[settings.MONGODB_DATABASE]

    @classmethod
    async def create_indexes(cls):
        """Create necessary performance and time-series indexes."""
        if cls.db is None:
            return
        
        try:
            # Users indexes
            await cls.db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            await cls.db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
            
            # Astronauts indexes
            await cls.db.astronauts.create_index([("astronaut_id", pymongo.ASCENDING)], unique=True)
            await cls.db.astronauts.create_index([("user_id", pymongo.ASCENDING)])
            await cls.db.astronauts.create_index([("mission_id", pymongo.ASCENDING)])

            # Missions indexes
            await cls.db.missions.create_index([("mission_code", pymongo.ASCENDING)], unique=True)

            # Devices indexes
            await cls.db.devices.create_index([("device_id", pymongo.ASCENDING)], unique=True)
            await cls.db.devices.create_index([("assigned_to", pymongo.ASCENDING)])

            # Sensor Telemetry (Time-Series performance indexes)
            await cls.db.sensor_readings.create_index([
                ("astronaut_id", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            await cls.db.sensor_readings.create_index([("timestamp", pymongo.DESCENDING)])

            # Environmental Telemetry indexes
            await cls.db.environmental_readings.create_index([
                ("compartment_id", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            await cls.db.environmental_readings.create_index([("timestamp", pymongo.DESCENDING)])

            # Alerts indexes
            await cls.db.health_alerts.create_index([
                ("astronaut_id", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING)
            ])
            await cls.db.health_alerts.create_index([("created_at", pymongo.DESCENDING)])
            await cls.db.health_alerts.create_index([("category", pymongo.ASCENDING)])

            # AI Predictions & Anomaly Indexes
            await cls.db.ai_predictions.create_index([
                ("astronaut_id", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])

            # Psychological Wellness Logs
            await cls.db.mental_health_logs.create_index([
                ("astronaut_id", pymongo.ASCENDING),
                ("date", pymongo.DESCENDING)
            ])

            # Audit Logs
            await cls.db.audit_logs.create_index([("timestamp", pymongo.DESCENDING)])

            logger.info("MongoDB collections and performance indexes successfully initialized.")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

# Helper dependency to get db in FastAPI
async def get_db() -> AsyncIOMotorDatabase:
    import asyncio
    current_loop = asyncio.get_running_loop()
    if DatabaseManager.db is None or DatabaseManager._loop is not current_loop:
        await DatabaseManager.connect()
    return DatabaseManager.db


class OfflineSQLiteManager:
    """Manages local SQLite database for offline buffering and synchronization."""
    
    @staticmethod
    def init_offline_db():
        """Initializes SQLite schema for edge/offline sensor reading buffer."""
        conn = sqlite3.connect(settings.OFFLINE_SQLITE_PATH)
        cursor = conn.cursor()
        
        # Sensor buffer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_sensor_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                astronaut_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                heart_rate REAL,
                hrv REAL,
                spo2 REAL,
                body_temp REAL,
                temp_measurement_type TEXT,
                motion_x REAL,
                motion_y REAL,
                motion_z REAL,
                activity_level TEXT,
                measurement_quality REAL,
                is_simulated INTEGER,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Environmental buffer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_environmental_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compartment_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                atmospheric_pressure REAL,
                co2_ppm REAL,
                voc_index REAL,
                radiation_dose_rate_uSv_h REAL,
                radiation_cumulative_mSv REAL,
                sensor_status TEXT,
                is_simulated INTEGER,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Sync log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_timestamp TEXT NOT NULL,
                records_uploaded INTEGER NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Local offline SQLite storage initialized at {settings.OFFLINE_SQLITE_PATH}")

    @staticmethod
    def get_connection():
        return sqlite3.connect(settings.OFFLINE_SQLITE_PATH)
