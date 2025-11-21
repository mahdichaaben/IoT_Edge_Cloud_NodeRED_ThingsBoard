import os
import json
import asyncio
import random
import logging
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("BROKER", "mosquitto")
PORT = int(os.getenv("PORT", 1883))
TOPIC_SENSOR = os.getenv("SENSOR_MOTION", "home/sensor/motion")
LOG_FILE = os.getenv("LOG_MOTION", "logs/motion.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

def on_connect(client, userdata, flags, rc, properties=None):
    logging.info(f"✅ Connected to broker with result code {rc}")
    print(f"✅ Connected to broker with result code {rc}")

async def publish_motion(client):
    while True:
        motion = random.choice([True, False])
        payload = {"motion": motion, "timestamp": current_timestamp()}
        res = client.publish(TOPIC_SENSOR, json.dumps(payload), qos=1)
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"🚶 Motion: {motion} | Payload: {payload}")
            print(f"🚶 Motion: {motion}")
        else:
            logging.error(f"⚠️ Failed to publish (rc={res.rc})")
        await asyncio.sleep(4)

async def main():
    client = mqtt.Client(client_id="motion_sensor", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    try:
        await publish_motion(client)
    except asyncio.CancelledError:
        logging.info("🛑 Motion sensor stopped.")
        print("🛑 Motion sensor stopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Motion sensor stopped by user.")
        print("Motion sensor stopped.")
