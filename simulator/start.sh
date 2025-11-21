#!/bin/bash

echo "🚀 Starting all MQTT scripts in parallel..."

# Start all sensors in background
python Sensors/humidity.py &
python Sensors/motion.py &
python Sensors/temperature.py &

# Start all actuators in background
python Actuators/fan.py &
python Actuators/lamp.py &
python Actuators/alarm.py &

# Wait for all background jobs
wait
