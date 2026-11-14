"""
AstroHealth Offline Storage and Synchronization Engine
Provides local edge buffering to SQLite when spacecraft communication or primary database
is offline, idempotent duplicate prevention, conflict resolution, and synchronization logs.
"""
import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

# Local SQLite database path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
project_root = backend_dir.parent
OFFLINE_DB_PATH = str(project_root / "astrohealth_offline_buffer.db")

logger = logging.getLogger("astrohealth.offline")


class OfflineSyncEngine:
    """
    Manages local SQLite edge storage for high-frequency telemetry buffering,
    offline health analysis, and seamless re-synchronization with primary database.
    """

    def __init__(self, db_path: str = OFFLINE_DB_PATH):
        self.db_path = db_path
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        """Ensure all required tables and indexes exist in local SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
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
                is_simulated INTEGER DEFAULT 0,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(astronaut_id, device_id, timestamp)
            )
        """)
        cursor.execute("""
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
                is_simulated INTEGER DEFAULT 0,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(compartment_id, device_id, timestamp)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_timestamp TEXT NOT NULL,
                records_uploaded INTEGER NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()

    def buffer_sensor_reading(self, reading: Dict[str, Any]) -> int:
        """
        Buffers a single biometric sensor reading to local SQLite edge storage.
        Uses INSERT OR IGNORE to prevent duplicate buffered entries.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        ts = reading.get("timestamp")
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        cursor.execute("""
            INSERT OR IGNORE INTO offline_sensor_buffer (
                astronaut_id, device_id, timestamp, heart_rate, hrv, spo2,
                body_temp, temp_measurement_type, motion_x, motion_y, motion_z,
                activity_level, measurement_quality, is_simulated, synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            reading.get("astronaut_id"),
            reading.get("device_id"),
            ts,
            reading.get("heart_rate"),
            reading.get("hrv"),
            reading.get("spo2"),
            reading.get("body_temp"),
            reading.get("temp_measurement_type", "epidermal_patch"),
            reading.get("motion_x", 0.0),
            reading.get("motion_y", 0.0),
            reading.get("motion_z", 0.0),
            reading.get("activity_level", "rest"),
            reading.get("measurement_quality", 0.98),
            1 if reading.get("is_simulated") else 0
        ))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def buffer_environmental_reading(self, reading: Dict[str, Any]) -> int:
        """Buffers an environmental pod reading to local SQLite edge storage."""
        conn = self._get_connection()
        cursor = conn.cursor()
        ts = reading.get("timestamp")
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        cursor.execute("""
            INSERT OR IGNORE INTO offline_environmental_buffer (
                compartment_id, device_id, timestamp, temperature, humidity,
                atmospheric_pressure, co2_ppm, voc_index, radiation_dose_rate_uSv_h,
                radiation_cumulative_mSv, sensor_status, is_simulated, synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            reading.get("compartment_id"),
            reading.get("device_id"),
            ts,
            reading.get("temperature"),
            reading.get("humidity"),
            reading.get("atmospheric_pressure"),
            reading.get("co2_ppm"),
            reading.get("voc_index", 100.0),
            reading.get("radiation_dose_rate_uSv_h"),
            reading.get("radiation_cumulative_mSv"),
            reading.get("sensor_status", "NOMINAL"),
            1 if reading.get("is_simulated") else 0
        ))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def get_buffer_status(self) -> Dict[str, Any]:
        """Returns statistics on pending unsynced records and storage volume."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM offline_sensor_buffer WHERE synced = 0")
        pending_biometrics = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM offline_sensor_buffer")
        total_biometrics = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM offline_environmental_buffer WHERE synced = 0")
        pending_environmental = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM offline_environmental_buffer")
        total_environmental = cursor.fetchone()["count"]

        cursor.execute("SELECT * FROM offline_sync_logs ORDER BY id DESC LIMIT 1")
        last_log = cursor.fetchone()

        conn.close()
        return {
            "status": "ready",
            "storage_engine": "SQLite",
            "db_path": self.db_path,
            "pending_sync": {
                "biometrics": pending_biometrics,
                "environmental": pending_environmental,
                "total_pending": pending_biometrics + pending_environmental
            },
            "total_records": {
                "biometrics": total_biometrics,
                "environmental": total_environmental
            },
            "last_sync": dict(last_log) if last_log else None
        }

    async def synchronize_with_mongodb(self, mongo_db) -> Dict[str, Any]:
        """
        Synchronizes all pending buffered records into primary MongoDB.
        Uses compound key ($setOnInsert upsert) to guarantee duplicate prevention.
        Updates SQLite status to synced = 1.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Fetch unsynced biometrics
        cursor.execute("SELECT * FROM offline_sensor_buffer WHERE synced = 0 LIMIT 1000")
        bio_rows = cursor.fetchall()

        synced_bio_ids = []
        bio_uploaded = 0

        for row in bio_rows:
            doc = dict(row)
            row_id = doc.pop("id")
            doc.pop("synced", None)
            doc.pop("created_at", None)
            doc["is_simulated"] = bool(doc.get("is_simulated"))

            # Convert timestamp to datetime
            try:
                doc["timestamp"] = datetime.fromisoformat(doc["timestamp"])
            except Exception:
                doc["timestamp"] = datetime.utcnow()

            # Upsert into MongoDB to prevent duplicates
            filter_query = {
                "astronaut_id": doc["astronaut_id"],
                "device_id": doc["device_id"],
                "timestamp": doc["timestamp"]
            }
            res = await mongo_db.sensor_readings.update_one(
                filter_query,
                {"$setOnInsert": doc},
                upsert=True
            )
            synced_bio_ids.append(row_id)
            if res.upserted_id or res.modified_count > 0:
                bio_uploaded += 1

        # 2. Fetch unsynced environmental
        cursor.execute("SELECT * FROM offline_environmental_buffer WHERE synced = 0 LIMIT 1000")
        env_rows = cursor.fetchall()

        synced_env_ids = []
        env_uploaded = 0

        for row in env_rows:
            doc = dict(row)
            row_id = doc.pop("id")
            doc.pop("synced", None)
            doc.pop("created_at", None)
            doc["is_simulated"] = bool(doc.get("is_simulated"))

            try:
                doc["timestamp"] = datetime.fromisoformat(doc["timestamp"])
            except Exception:
                doc["timestamp"] = datetime.utcnow()

            filter_query = {
                "compartment_id": doc["compartment_id"],
                "device_id": doc["device_id"],
                "timestamp": doc["timestamp"]
            }
            res = await mongo_db.environmental_readings.update_one(
                filter_query,
                {"$setOnInsert": doc},
                upsert=True
            )
            synced_env_ids.append(row_id)
            if res.upserted_id or res.modified_count > 0:
                env_uploaded += 1

        # 3. Mark synchronized records in SQLite
        if synced_bio_ids:
            cursor.execute(f"UPDATE offline_sensor_buffer SET synced = 1 WHERE id IN ({','.join(['?']*len(synced_bio_ids))})", synced_bio_ids)
        if synced_env_ids:
            cursor.execute(f"UPDATE offline_environmental_buffer SET synced = 1 WHERE id IN ({','.join(['?']*len(synced_env_ids))})", synced_env_ids)

        total_synced = len(synced_bio_ids) + len(synced_env_ids)
        now_iso = datetime.utcnow().isoformat()

        # 4. Insert sync log in SQLite
        cursor.execute("""
            INSERT INTO offline_sync_logs (sync_timestamp, records_uploaded, status, details)
            VALUES (?, ?, ?, ?)
        """, (
            now_iso,
            total_synced,
            "SUCCESS",
            json.dumps({"biometrics_synced": len(synced_bio_ids), "environmental_synced": len(synced_env_ids)})
        ))

        conn.commit()
        conn.close()

        # 5. Insert sync log in MongoDB
        await mongo_db.device_sync_logs.insert_one({
            "sync_timestamp": datetime.utcnow(),
            "records_uploaded": total_synced,
            "biometrics_count": len(synced_bio_ids),
            "environmental_count": len(synced_env_ids),
            "status": "SUCCESS"
        })

        logger.info(f"Offline sync complete: {total_synced} records updated into primary MongoDB.")
        return {
            "status": "SUCCESS",
            "synced_biometrics": len(synced_bio_ids),
            "synced_environmental": len(synced_env_ids),
            "total_synced": total_synced,
            "timestamp": now_iso
        }


offline_sync_engine = OfflineSyncEngine()
