FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Actuators/ Actuators/
COPY Sensors/ Sensors/
COPY .env .env

COPY start.sh .
RUN apt-get update && apt-get install -y dos2unix && dos2unix start.sh && apt-get remove -y dos2unix && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
RUN chmod +x start.sh

CMD ["./start.sh"]
