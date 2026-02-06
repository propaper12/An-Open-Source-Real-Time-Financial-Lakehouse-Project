import time
import subprocess
import os
from deltalake import DeltaTable

# AYARLAR
MIN_ROWS_TO_START = 20       
NORMAL_INTERVAL_SEC = 5 * 60 

DATA_PATH = "s3://market-data/silver_layer_delta"

# MinIO Bağlantı Ayarları
storage_options = {
    "AWS_ACCESS_KEY_ID": "admin",
    "AWS_SECRET_ACCESS_KEY": "admin12345",
    "AWS_ENDPOINT_URL": "http://minio:9000",
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    "AWS_ALLOW_HTTP": "true"
}

print(f" ML Watcher  Başladı - Hedef: {MIN_ROWS_TO_START} Satır")

first_training_done = False

def get_row_count():
    """MinIO'daki Delta tablosunu okur"""
    try:
        # DeltaTable'ı MinIO ayarlarıyla yükle
        dt = DeltaTable(DATA_PATH, storage_options=storage_options)
        
        # Pandas DataFrame'e çevirip say
        count = len(dt.to_pandas())
        return count
    except Exception as e:
        # Eğer tablo henüz oluşmadıysa veya _delta_log yoksa hata verir
        # Bu normaldir, Spark henüz commit etmemiş olabilir
        # print(f" Okuma Hatası (Henüz veri yok mu?): {e}") 
        return 0

def run_training():
    print(f"\n EĞİTİM TETİKLENDİ Saat: {time.strftime('%H:%M:%S')}")
    try:
        result = subprocess.run(["python", "train_model.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(" Eğitim Başarıyla Tamamlandı")
            print(f"Log Sonu:{result.stdout[-200:]}")
            return True
        else:
            print("Eğitimde Hata Oldu")
            print(result.stderr)
            return False
    except Exception as e:
        print(f" Sistem Hatası:{e}")
        return False

# ANA DÖNGÜ 
while True:
    current_rows = get_row_count()
    
    if not first_training_done:
        # MOD 1: AVCI MODU
        if current_rows >= MIN_ROWS_TO_START:
            print(f" HEDEF ULAŞILDI! ({current_rows}/{MIN_ROWS_TO_START} satır). İlk eğitim başlıyor...")
            success = run_training()
            if success:
                first_training_done = True
                print(f" İlk eğitim bitti. Artık {int(NORMAL_INTERVAL_SEC/60)} dakikada bir çalışacağım.")
        else:
            print(f"⏳ Veri Bekleniyor... Mevcut: {current_rows}/{MIN_ROWS_TO_START} (Kontrol: 10sn)")
            time.sleep(10) 
            
    else:
        # MOD 2: DEVRİYE MODU
        print(f"💤 Uyku Modu ({int(NORMAL_INTERVAL_SEC/60)} dk)... Zzz...")
        time.sleep(NORMAL_INTERVAL_SEC)
        
        # Uyanınca tekrar kontrol et
        current_rows = get_row_count()
        print(f" Vakit geldi Veri durumu: {current_rows} satır.")

        run_training()
