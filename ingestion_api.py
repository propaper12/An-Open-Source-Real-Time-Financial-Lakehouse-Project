from fastapi import FastAPI, HTTPException, Request
from kafka import KafkaProducer
import json
import os
import time

app = FastAPI()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = 'market_data'

producer = None


def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVER,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            print(" API Gateway: Kafka Bağlantısı Başarılı!")
        except Exception as e:
            print(f" Kafka Bağlantı Hatası: {e}")
    return producer


@app.post("/api/v1/ingest")
async def ingest_data(request: Request):
    """
    Şirketler verilerini buraya POST edecek.
    Beklenen Format:
    {
        "symbol": "COMPANY_X",
        "price": 100.5,
        "quantity": 50,
        "timestamp": "2023-10-27T10:00:00"
    }
    """
    data = await request.json()

    required_fields = ["symbol", "price", "timestamp"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Eksik veri! (symbol, price, timestamp gerekli)")

    if "quantity" not in data:
        data["quantity"] = 1.0

    try:
        kafka = get_kafka_producer()
        if kafka:
            kafka.send(KAFKA_TOPIC, value=data)
            return {"status": "success", "message": "Veri kuyruğa alındı"}
        else:
            raise HTTPException(status_code=500, detail="Kafka bağlantısı yok")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))