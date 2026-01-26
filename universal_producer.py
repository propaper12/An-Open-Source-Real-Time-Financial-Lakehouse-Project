import time
import json
import os
import sys
import logging
import random
import math
from datetime import datetime
from kafka import KafkaProducer

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'market_data'
LOG_FILE = "/app/producer_activity.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    filemode='w',
    force=True
)

def get_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
    except Exception as e:
        logging.error(f"Kafka Hatası: {e}")
        return None

def generate_universal_data(data_type, identity, counter):
    """
    Her türlü veri tipi için mantıklı değerler üretir.
    Dönüş: (Ana Değer, Yan Değer, Kaynak Tipi)
    """
    
    if "Sensor" in data_type or "IoT" in data_type:
        base_val = 25
        fluctuation = math.sin(counter / 10) * 10  
        val1 = base_val + fluctuation + random.uniform(-2, 2) 
        val2 = 50 + random.uniform(-10, 10) 
        return round(val1, 2), int(val2), "IoT_Device"

    elif "Server" in data_type or "CPU" in data_type:
        val1 = random.uniform(10, 95) 
        val2 = val1 * 0.6 + random.uniform(2, 5) 
        return round(val1, 2), int(val2), "System_Metric"

    elif "Web" in data_type or "Trafik" in data_type:
        val1 = random.uniform(500, 5000) 
        val2 = val1 / 10 + random.uniform(-50, 50) 
        return int(val1), int(val2), "Web_Analytics"

    elif "Borsa" in data_type or "Finance" in data_type:
        trend = math.cos(counter / 20) * 20
        val1 = 100 + trend + random.uniform(-5, 5) 
        val2 = random.randint(100, 10000) 
        return round(val1, 2), int(val2), "Financial_Feed"

    else:
        val1 = random.uniform(0, 100)
        val2 = random.uniform(0, 100)
        return round(val1, 2), round(val2, 2), "Generic_Data"

def start_stream(data_type, device_id):
    producer = get_producer()
    if not producer:
        return

    start_msg = f"🔌 EVRENSEL AKIŞ BAŞLADI: [{data_type}] -> ID: {device_id}"
    print(start_msg)
    logging.info(start_msg)
    
    counter = 0
    
    while True:
        try:
            val1, val2, source_type = generate_universal_data(data_type, device_id, counter)

            data = {
                "symbol": device_id,
                "price": val1,
                "quantity": val2,
                "timestamp": datetime.utcnow().isoformat(),
                "source": source_type,
                "api_key_used": "universal_key"
            }
            
            producer.send(TOPIC, value=data)
            
            log_msg = f"📡 {device_id}: {val1} | Yan Veri: {val2} [{source_type}]"
            print(log_msg)
            logging.info(log_msg)
            
            counter += 1
            time.sleep(1) 
            
        except KeyboardInterrupt:
            logging.info("⛔ Akış durduruldu.")
            break
        except Exception as e:
            logging.error(f"Hata: {e}")
            time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        dtype = sys.argv[1]
        did = sys.argv[2]
        start_stream(dtype, did)
    else:
        logging.error("Eksik parametre")