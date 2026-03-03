import json
import time
import os
import websocket
import logging
from kafka import KafkaProducer
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = 'market_data'

def get_kafka_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVER,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                acks=1, 
                retries=5, 
                compression_type='gzip' 
            )
            logger.info("Kafka bağlantısı başarıyla kuruldu.")
            return producer
        except Exception as e:
            logger.error(f"Kafka'ya bağlanılamadı, 5 saniye sonra tekrar denenecek: {e}")
            time.sleep(5)

producer = get_kafka_producer()

def on_message(ws, message):
    try:
        raw_message = json.loads(message)
        
        # MULTI-STREAM GÜNCELLEMESİ (10 Coin için Json Ayrıştırma)
        # Binance birden fazla coin olunca veriyi "data" anahtarı içine koyar.
        data = raw_message.get('data', raw_message)
        
        processed_data = {
            'symbol': data['s'], 
            'price': float(data['p']),
            'quantity': float(data['q']),
            'timestamp': datetime.fromtimestamp(data['T'] / 1000).isoformat(),
            'event_time': datetime.utcnow().isoformat(),
            'source': 'binance_ws'
        }
        
        producer.send(KAFKA_TOPIC, value=processed_data)

    except Exception as e:
        logger.error(f"Veri işleme hatası: {e}")

def on_error(ws, error):
    logger.error(f"WebSocket hatası saptandı: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning("Baglanti kapandi. Yeniden baglanma sureci baslatiliyor.")
    time.sleep(2) 

def on_open(ws):
    logger.info("Binance Multi-Stream baglantisi acildi. 10 Coinlik veri akisi basliyor.")

if __name__ == "__main__":
    # 10 COİNLİK LİSTE (İstediğin gibi değiştirebilirsin)
    coins = ["btcusdt", "ethusdt", "solusdt", "xrpusdt", "avaxusdt", "bnbusdt", "adausdt", "dogeusdt", "dotusdt", "linkusdt"]
    
    # Binance Multi-Stream URL formatını oluşturuyoruz
    streams = "/".join([f"{coin}@trade" for coin in coins])
    socket_url = f"wss://stream.binance.com:9443/stream?streams={streams}"

    while True:
        ws = websocket.WebSocketApp(
            socket_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever(ping_interval=70, ping_timeout=10)