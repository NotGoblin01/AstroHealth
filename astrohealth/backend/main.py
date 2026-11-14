"""
AstroHealth FastAPI Application Entrypoint
Provides REST endpoints, WebSocket connections, lifecycle management, and security.
"""
import sys
import asyncio
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import DatabaseManager, OfflineSQLiteManager
from routers import auth, users, astronauts, missions, devices, telemetry, simulator, ai, reports, wellness, alerts, offline
from services.websocket_service import broadcaster
from seed import seed_database

# Hardware & Simulation services
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "simulator"))
sys.path.insert(0, str(project_root / "hardware"))

from engine import simulator_engine
from mqtt_bridge import mqtt_bridge
from routers.simulator import handle_simulation_frame

# Configure Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("astrohealth.main")


class WebSocketManager:
    """Manages active WebSocket connections for real-time telemetry and alerts."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead_conn in disconnected:
            self.disconnect(dead_conn)


ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events: startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}...")
    # Initialize MongoDB
    await DatabaseManager.connect()
    
    # Initialize Offline SQLite
    OfflineSQLiteManager.init_offline_db()

    # Check and run automatic seed data if database is empty
    try:
        db = DatabaseManager.get_sync_db()
        if db.users.count_documents({}) == 0:
            logger.info("Empty database detected. Running automatic initial seeding...")
            seed_database()
    except Exception as e:
        logger.warning(f"Seed check error: {e}")

    # Start Hardware MQTT Bridge
    try:
        mqtt_bridge.start(lambda f_type, data: asyncio.create_task(handle_simulation_frame(f_type, data)))
    except Exception as e:
        logger.warning(f"MQTT Bridge init note: {e}")

    # Start Simulation Engine if enabled
    if settings.SIMULATION_MODE:
        logger.info("Auto-starting Hardware Sensor Simulation Engine...")
        simulator_engine.start(handle_simulation_frame)

    yield

    logger.info("Shutting down AstroHealth services...")
    simulator_engine.stop()
    mqtt_bridge.stop()
    await DatabaseManager.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Health & Environmental Monitoring Beyond Earth",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(astronauts.router)
app.include_router(missions.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(simulator.router)
app.include_router(ai.router)
app.include_router(reports.router)
app.include_router(wellness.router)
app.include_router(alerts.router)
app.include_router(offline.router)


@app.get("/api/health", tags=["System"])
async def health_check():
    """System status and diagnostics endpoint."""
    mongo_status = "connected" if DatabaseManager.client else "disconnected"
    return {
        "status": "operational",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "type": "MongoDB",
            "status": mongo_status,
            "database_name": settings.MONGODB_DATABASE
        },
        "offline_storage": {
            "type": "SQLite",
            "status": "ready",
            "path": settings.OFFLINE_SQLITE_PATH
        },
        "simulation_mode": settings.SIMULATION_MODE,
        "active_ws_subscribers": len(ws_manager.active_connections)
    }


@app.get("/api/info", tags=["System"])
async def system_info():
    """Returns mission, crew, and platform metadata."""
    return {
        "mission": "Project Ares-V",
        "tagline": "Intelligent Health Monitoring Beyond Earth",
        "supported_sensors": [
            "MAX30102 (Heart Rate, SpO2)",
            "MPU6050 (3-Axis IMU & Activity)",
            "DS18B20 (Continuous Core/Skin Body Temp)",
            "BME680 (Atmospheric Pressure, Temp, Humidity, VOC)",
            "SCD41 (Photoacoustic Carbon Dioxide)",
            "Silicon Solid-State Radiation Dosimeter"
        ],
        "ai_engine": {
            "anomaly_detection": "Isolation Forest (scikit-learn)",
            "explainability": "SHAP feature contribution",
            "experimental_classification": "Random Forest",
            "cardiovascular_trends": "Statistical sliding-window analysis"
        }
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Real-time biometrics, environmental telemetry, and alerts stream."""
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep alive and receive optional client messages/subscriptions
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "payload": data})
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        broadcaster.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
