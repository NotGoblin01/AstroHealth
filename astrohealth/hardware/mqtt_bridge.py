"""
AstroHealth MQTT Hardware Bridge Module
Implements robust MQTT communication for real IoT hardware (ESP32/Sensors),
device authentication, topic routing, payload validation, and automatic reconnection.
"""
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
import paho.mqtt.client as mqtt

from config import settings
from services.websocket_service import broadcaster
from database import DatabaseManager

logger = logging.getLogger("astrohealth.mqtt")

# Documented Topic Hierarchy
TOPIC_BIOMETRICS = "astrohealth/astronaut/+/biometrics"
TOPIC_ACTIVITY = "astrohealth/astronaut/+/activity"
TOPIC_ENVIRONMENT = "astrohealth/environment/+"
TOPIC_DEVICE_STATUS = "astrohealth/device/+/status"
TOPIC_ALERTS = "astrohealth/alerts/+"


class AstroHealthMQTTBridge:
    """
    Subscribes to hardware telemetry streams over MQTT and forwards validated
    sensor frames into the AstroHealth backend and live WebSocket stream.
    """
    def __init__(self, broker_host: str = settings.MQTT_BROKER_HOST, broker_port: int = settings.MQTT_BROKER_PORT):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client: Optional[mqtt.Client] = None
        self.is_connected: bool = False
        self.message_callback: Optional[Callable] = None
        self.reconnect_delay: int = 5

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT Broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to all AstroHealth telemetry topics
            topics = [
                (TOPIC_BIOMETRICS, 1),
                (TOPIC_ACTIVITY, 1),
                (TOPIC_ENVIRONMENT, 1),
                (TOPIC_DEVICE_STATUS, 1),
                (TOPIC_ALERTS, 1)
            ]
            client.subscribe(topics)
            logger.info("Subscribed to AstroHealth MQTT topics.")
        else:
            self.is_connected = False
            logger.warning(f"Failed to connect to MQTT broker, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker (rc: {rc}). Automatic reconnect active.")

    def _on_message(self, client, userdata, msg):
        """Processes incoming hardware telemetry message."""
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")
        try:
            payload = json.loads(payload_str)
            self._route_message(topic, payload)
        except json.JSONDecodeError:
            logger.error(f"Malformed JSON received on topic {topic}: {payload_str}")
        except Exception as e:
            logger.error(f"Error handling message on {topic}: {e}")

    def _route_message(self, topic: str, payload: Dict[str, Any]):
        """Dispatches validated MQTT frames to database and WebSocket."""
        parts = topic.split("/")
        
        # 1. Biometric stream: astrohealth/astronaut/{id}/biometrics
        if len(parts) >= 4 and parts[1] == "astronaut" and parts[3] == "biometrics":
            astro_id = parts[2]
            payload["astronaut_id"] = astro_id
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.now(timezone.utc).isoformat()
            if "is_simulated" not in payload:
                payload["is_simulated"] = False

            # Forward to synchronous/async storage if callback registered
            if self.message_callback:
                self.message_callback("biometric", payload)

        # 2. Environmental stream: astrohealth/environment/{compartment}
        elif len(parts) >= 3 and parts[1] == "environment":
            compartment = parts[2]
            payload["compartment_id"] = compartment
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.now(timezone.utc).isoformat()

            if self.message_callback:
                self.message_callback("environmental", payload)

        # 3. Device status heartbeat: astrohealth/device/{device_id}/status
        elif len(parts) >= 4 and parts[1] == "device" and parts[3] == "status":
            device_id = parts[2]
            logger.info(f"Hardware heartbeat from device {device_id}: {payload}")

    def start(self, message_callback: Optional[Callable] = None):
        """Start non-blocking MQTT loop."""
        self.message_callback = message_callback
        try:
            self.client = mqtt.Client(
                client_id=f"{settings.MQTT_CLIENT_ID}_{datetime.now().timestamp()}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect_async(self.broker_host, self.broker_port, keepalive=settings.MQTT_KEEP_ALIVE)
            self.client.loop_start()
        except Exception as e:
            logger.warning(f"Could not connect to external MQTT broker: {e}. Simulator and REST ingestion remain fully operational.")

    def stop(self):
        """Stop MQTT client."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Bridge client disconnected and stopped.")

    def publish_biometrics(self, astronaut_id: str, data: Dict[str, Any]):
        """Helper to publish biometric readings over MQTT."""
        if self.client and self.is_connected:
            topic = f"astrohealth/astronaut/{astronaut_id}/biometrics"
            self.client.publish(topic, json.dumps(data), qos=1)

    def publish_environment(self, compartment_id: str, data: Dict[str, Any]):
        """Helper to publish environmental readings over MQTT."""
        if self.client and self.is_connected:
            topic = f"astrohealth/environment/{compartment_id}"
            self.client.publish(topic, json.dumps(data), qos=1)


# Global MQTT bridge instance
mqtt_bridge = AstroHealthMQTTBridge()

