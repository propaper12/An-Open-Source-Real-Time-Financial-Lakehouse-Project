import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime

# Kafka Ayarları
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# FABRİKA ENVANTERİ (Gerçekçilik için sabit cihazlar)
DEVICES = [
    {"id": "ROBOT-ARM-01", "location": "Factory_A", "type": "Welder", "firmware": "v2.1"},
    {"id": "CONVEYOR-BELT-04", "location": "Factory_A", "type": "Motor", "firmware": "v1.0"},
    {"id": "PAINT-SPRAYER-02", "location": "Factory_B", "type": "Sprayer", "firmware": "v3.5"},
    {"id": "HVAC-MAIN-01", "location": "Roof_1", "type": "Climate", "firmware": "v1.2"},
]

print("🏭 ENDÜSTRİYEL IOT SİMÜLASYONU BAŞLIYOR (MQTT -> KAFKA)...")

try:
    while True:
        # Rastgele bir cihaz seç
        device = random.choice(DEVICES)
        
        # SİMÜLASYON 1: Sensör "Drift"i (Hafif Dalgalanma)
        base_temp = 65.0 if device['type'] == 'Welder' else 25.0
        current_temp = base_temp + random.uniform(-2.0, 2.0)

        # SİMÜLASYON 2: Arıza Durumu (Outlier)
        # %1 ihtimalle sensör bozuk veri yollar (Anomaly Detection için harika test verisidir)
        if random.random() < 0.01:
            current_temp = 999.9 
            status = "ERROR"
            error_code = "E-501"
        else:
            status = "OK"
            error_code = None

        # SİMÜLASYON 3: Batarya Tüketimi
        battery = round(random.uniform(10.0, 100.0), 1)

        # Payload (Paket) Oluşturma
        iot_payload = {
            "device_id": device['id'],
            "factory_loc": device['location'],  
            "sensor_type": device['type'],
            "readings": {
                "temperature": round(current_temp, 2),
                "vibration": round(random.uniform(0.1, 5.0), 3),
                "rpm": random.randint(1000, 5000) if device['type'] == 'Motor' else 0
            },
            "diagnostics": {
                "battery_level": battery,
                "status": status,
                "error_code": error_code,
                "uptime_seconds": random.randint(100, 99999)
            },
            "event_time": datetime.utcnow().isoformat(),
            "data_type": "IOT" # Bizim Generic etiketi
        }

        producer.send('market_data', value=iot_payload)
        
        if status == "ERROR":
            print(f" KRİTİK HATA: {device['id']} -> 999.9°C")
        else:
            print(f" Veri yollandı: {device['id']} | Temp: {iot_payload['readings']['temperature']}")

        time.sleep(0.5) # Saniyede 2 veri (Gerçekçi hız)

except KeyboardInterrupt:
    print("Simülasyon durduruldu.")