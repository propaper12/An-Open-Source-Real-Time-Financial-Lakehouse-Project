import time
import subprocess
import os
import redis
from deltalake import DeltaTable

MIN_ROWS_TO_START = 20       
NORMAL_INTERVAL_SEC = 5 * 60 
DATA_PATH = "s3://market-data/silver_layer_delta"

storage_options = {
    "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER", "admin"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
    "AWS_ENDPOINT_URL": os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    "AWS_ALLOW_HTTP": "true"
}

print(f"MLOps Orchestrator (Watcher) başlatıldı. Eşik değeri: {MIN_ROWS_TO_START} satır.")
first_training_done = False

def get_row_count():
    try:
        dt = DeltaTable(DATA_PATH, storage_options=storage_options)
        return len(dt.to_pandas())
    except Exception:
        return 0

def run_training():
    print(f"Eğitim tetiklendi. Zaman damgası: {time.strftime('%H:%M:%S')}")
    try:
        result = subprocess.run(["python", "train_model.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Eğitim başarıyla tamamlandı ve model MLflow Registry üzerine kaydedildi.")
            
            # --- REDIS PUB/SUB İLE SİNYAL GÖNDERME ---
            try:
                print("FastAPI Worker'larına modelleri yenilemesi için Redis Pub/Sub sinyali gönderiliyor...")
                r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)
                r.publish("model_updates", "RELOAD_MODELS")
                print("✅ API cache tazelendi. Sistem yeni modellerle tahmin üretmeye hazır.")
            except Exception as e:
                print(f"Redis Pub/Sub ile iletişim kurulamadı: {e}")
                
            return True
        else:
            print("Eğitim sürecinde hata saptandı:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Orkestrasyon sırasında sistem hatası: {e}")
        return False

while True:
    current_rows = get_row_count()
    
    if not first_training_done:
        if current_rows >= MIN_ROWS_TO_START:
            print(f"Hedef veri hacmine ulaşıldı ({current_rows}/{MIN_ROWS_TO_START}). İlk döngü başlatılıyor.")
            if run_training():
                first_training_done = True
                print(f"İlk eğitim başarılı. Periyodik kontrol moduna ({int(NORMAL_INTERVAL_SEC/60)} dk) geçiliyor.")
        else:
            print(f"Veri birikmesi bekleniyor. Mevcut durum: {current_rows}/{MIN_ROWS_TO_START}")
            time.sleep(10) 
            
    else:
        time.sleep(NORMAL_INTERVAL_SEC)
        current_rows = get_row_count()
        print(f"Periyodik kontrol zamanı geldi. Mevcut satır sayısı: {current_rows}. Güncel eğitim başlatılıyor.")
        run_training()