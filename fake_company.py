import requests
import time
import random
from datetime import datetime

# Senin API adresin (Gerçek hayatta burası api.sirketim.com olur)
API_URL = "http://localhost:8000/api/v1/ingest"

# Hangi şirketi taklit ediyoruz?
COMPANY_SYMBOL = "TESLA_FACTORY"

print(f"📡 {COMPANY_SYMBOL} veri akışı başlatılıyor -> {API_URL}")

while True:
    try:
        # 1. Rastgele bir borsa verisi üretelim
        price = 240 + random.uniform(-5, 5)  # 235$ ile 245$ arası
        quantity = random.randint(1, 100)

        # 2. Gönderilecek JSON paketi
        payload = {
            "symbol": COMPANY_SYMBOL,
            "price": round(price, 2),
            "quantity": quantity,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 3. Senin API'ye POST isteği at (Veriyi fırlat)
        response = requests.post(API_URL, json=payload)

        # 4. Sonucu yazdır
        if response.status_code == 200:
            print(f" Gönderildi: {payload['price']} $ | Cevap: {response.json()}")
        else:
            print(f" Hata: {response.status_code} - {response.text}")

    except Exception as e:
        print(f" Bağlantı Hatası: {e}")
        print("API çalışıyor mu? (Docker'daki api-gateway servisi)")

    # 1 saniye bekle (Gerçekçi olsun)
    time.sleep(1)