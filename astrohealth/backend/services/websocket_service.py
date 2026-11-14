"""
AstroHealth WebSocket Broadcaster Service
Provides decoupled real-time pub/sub delivery for biometrics, environmental metrics, and alerts.
"""
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("astrohealth.websocket")

class TelemetryBroadcaster:
    active_connections: List[WebSocket] = []

    @classmethod
    async def connect(cls, websocket: WebSocket):
        await websocket.accept()
        cls.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(cls.active_connections)}")

    @classmethod
    def disconnect(cls, websocket: WebSocket):
        if websocket in cls.active_connections:
            cls.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(cls.active_connections)}")

    @classmethod
    async def broadcast(cls, message: Dict[str, Any]):
        disconnected = []
        for connection in cls.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead_conn in disconnected:
            cls.disconnect(dead_conn)

broadcaster = TelemetryBroadcaster

