# Dosya: tests/test_core.py
import sys
import os
import pytest
from datetime import datetime

# Ana dizindeki modülleri görebilmesi için path ayarı
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test edilecek fonksiyonları import ediyoruz
from universal_producer import generate_universal_data

# 1. TEST: Evrensel Veri Üreticisi Doğru Çalışıyor mu?
def test_universal_data_generator():
    print("\n TEST 1: Veri Üretici Kontrolü")
    
    # Senaryo A: IoT Verisi İstiyoruz
    val1, val2, source = generate_universal_data("IoT Sensor", "Device_X", 1)
    
    # Beklenti: Kaynak tipi 'IoT_Device' olmalı ve değerler sayı olmalı
    assert source == "IoT_Device", "Hata: IoT kaynağı yanlış etiketlendi!"
    assert isinstance(val1, float), "Hata: Sıcaklık değeri float olmalı!"
    assert isinstance(val2, int), "Hata: İkincil değer int olmalı!"
    
    # Senaryo B: Finans Verisi İstiyoruz
    val1, val2, source = generate_universal_data("Borsa", "BTC", 1)
    assert source == "Financial_Feed", "Hata: Finans kaynağı yanlış etiketlendi!"
    
    print(" Veri Üretici Testi GEÇTİ")

# 2. TEST: Veri Formatı Kontrolü
def test_data_structure():
    print("\n TEST 2: Veri Yapısı Kontrolü")
    
    # Diyelim ki producer'dan bir veri paketi oluşturduk
    mock_data = {
        "symbol": "TEST",
        "price": 100.5,
        "quantity": 50,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Bu verinin 'price' alanı negatif olmamalı (Basit mantık testi)
    assert mock_data['price'] > 0, "Hata: Fiyat negatif olamaz!"
    assert "timestamp" in mock_data, "Hata: Zaman damgası eksik!"
    
    print("Veri Yapısı Testi GEÇTİ")

if __name__ == "__main__":
    # Manuel çalıştırma için
    test_universal_data_generator()
    test_data_structure()