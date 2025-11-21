import os
import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("BROKER", "mosquitto")
PORT = int(os.getenv("PORT", 1883))
TOPIC_CMD = os.getenv("ALARM_TOPIC_CMD", "home/alarm/command")
TOPIC_STATE = os.getenv("ALARM_TOPIC_STATE", "home/alarm/state")

state = "OFF"
message_queue = asyncio.Queue()


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"✅ Connected to broker {BROKER}:{PORT} with result code {rc}")
    client.subscribe(TOPIC_CMD, qos=1)


def on_message(client, userdata, msg):
    # Correct usage: userdata contains the asyncio loop
    loop = userdata["loop"]
    asyncio.run_coroutine_threadsafe(message_queue.put(msg), loop)


async def handle_message(client):
    global state
    while True:
        msg = await message_queue.get()

        try:
            data = json.loads(msg.payload.decode())
            command = data.get("command", "").upper()
            msg_text = data.get("message", "Emergency!")

            if command == "TRIGGER":
                state = "ON"
                print(f"🚨 Emergency Alarm TRIGGERED: {msg_text}")
            elif command == "RESET":
                state = "OFF"
                print("✅ Emergency Alarm RESET")
            elif command == "SILENCE":
                state = "SILENCED"
                print("🔕 Alarm SILENCED")
            else:
                print(f"ℹ️ Unknown command: {command}")
                continue

            # State to publish
            status_msg = {
                "state": state,
                "timestamp": current_timestamp(),
                "message": msg_text,
            }

            res = client.publish(TOPIC_STATE, json.dumps(status_msg), qos=1)
            if res.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Published state: {status_msg}")
            else:
                print(f"⚠️ Failed to publish state (rc={res.rc})")

        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    loop = asyncio.get_running_loop()

    client = mqtt.Client(
        client_id="alarm_actuator",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    # CORRECT way to attach asyncio loop to userdata
    client.user_data_set({"loop": loop})

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # Wait for connection to establish
    await asyncio.sleep(1)

    try:
        await handle_message(client)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Alarm actuator stopped by user.")
    