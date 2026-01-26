import json
import time
import os
import websocket
from kafka import KafkaProducer
from datetime import datetime

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')
KAFKA_TOPIC = 'market_data'

print(f"Producer Başlatılıyor... Hedef: {KAFKA_SERVER}")

producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        print("Kafka Bağlantısı Başarılı!")
    except Exception as e:
        print(f"Kafka'ya bağlanılamadı, 5 saniye sonra tekrar denenecek... Hata: {e}")
        time.sleep(5)

def on_message(ws, message):
    try:
        data = json.loads(message)
        processed_data = {
            'symbol': 'BTCUSDT',
            'price': float(data['p']),
            'quantity': float(data['q']),
            'timestamp': datetime.fromtimestamp(data['T'] / 1000).isoformat()
        }
        producer.send(KAFKA_TOPIC, value=processed_data)
    except Exception as e:
        print(f"Veri işleme hatası: {e}")

def on_error(ws, error):
    print(f"WebSocket Hatası: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Bağlantı Kapandı. Yeniden bağlanılıyor...")

def on_open(ws):
    print("Binance WebSocket Bağlandı - Veri Akışı Başladı ")

if __name__ == "__main__":
    while True:
        try:
            socket_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
            ws = websocket.WebSocketApp(socket_url,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
            ws.run_forever()
        except Exception as e:
            print(f"Ana döngü hatası: {e}")
            time.sleep(5)