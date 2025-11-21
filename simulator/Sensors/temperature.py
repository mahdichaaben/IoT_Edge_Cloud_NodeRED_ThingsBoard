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
TOPIC_SENSOR = os.getenv("SENSOR_TEMPERATURE", "home/sensor/temperature")
LOG_FILE = os.getenv("LOG_TEMPERATURE", "logs/temperature.log")

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

async def publish_temperature(client):
    while True:
        temp = round(random.uniform(20.0, 30.0), 2)
        payload = {"temperature": temp, "unit": "°C", "timestamp": current_timestamp()}
        res = client.publish(TOPIC_SENSOR, json.dumps(payload), qos=1)
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"🌡️ Temperature: {temp} °C | Payload: {payload}")
            print(f"🌡️ Temperature: {temp} °C")
        else:
            logging.error(f"⚠️ Failed to publish (rc={res.rc})")
        await asyncio.sleep(5)

async def main():
    client = mqtt.Client(client_id="temperature_sensor", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    try:
        await publish_temperature(client)
    except asyncio.CancelledError:
        logging.info("🛑 Temperature sensor stopped.")
        print("🛑 Temperature sensor stopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Temperature sensor stopped by user.")
        print("Temperature sensor stopped.")
