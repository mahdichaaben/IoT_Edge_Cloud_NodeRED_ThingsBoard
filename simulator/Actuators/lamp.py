import os
import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# MQTT Configuration
BROKER = os.getenv("BROKER", "mosquitto")
PORT = int(os.getenv("PORT", 1883))
TOPIC_CMD = os.getenv("LAMP_TOPIC_CMD", "home/lamp/command")
TOPIC_STATE = os.getenv("LAMP_TOPIC_STATE", "home/lamp/state")

# Actuator state
state = "OFF"

# Async message queue
message_queue = asyncio.Queue()


# Utility
def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


# MQTT callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"✅ Connected to broker {BROKER}:{PORT} with result code {rc}")
    client.subscribe(TOPIC_CMD, qos=1)


def on_message(client, userdata, msg):
    asyncio.run_coroutine_threadsafe(message_queue.put(msg), userdata["loop"])


# Handle incoming commands
async def handle_message(client):
    global state
    while True:
        msg = await message_queue.get()
        try:
            data = json.loads(msg.payload.decode())
            command = data.get("command", "").upper()

            if command == "ON":
                state = "ON"
                print("💡 Lamp turned ON")
            elif command == "OFF":
                state = "OFF"
                print("💡 Lamp turned OFF")
            else:
                print(f"ℹ️ Unknown command: {command}")
                continue

            # Publish current state
            status_msg = {
                "state": state,
                "timestamp": current_timestamp()
            }
            res = client.publish(TOPIC_STATE, json.dumps(status_msg), qos=1)
            if res.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Published state: {status_msg}")
            else:
                print(f"⚠️ Failed to publish state (rc={res.rc})")

        except Exception as e:
            print(f"❌ Error: {e}")


# Main async routine
async def main():
    loop = asyncio.get_running_loop()
    client = mqtt.Client(
        client_id="lamp_actuator",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        userdata={"loop": loop}
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    try:
        await handle_message(client)
    except asyncio.CancelledError:
        print("🛑 Lamp actuator stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Lamp actuator stopped by user.")
