from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.sklearn
import os
import pandas as pd
import asyncio
import redis.asyncio as aioredis

app = FastAPI(title="MLOps Inference API", description="Real-time Crypto Price Prediction with Pub/Sub")

# MLflow Ayarları
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow_server:5000")
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("MINIO_ROOT_USER", "admin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Modeli RAM'de tutacağımız global değişken
model_cache = {}

# --- REDIS PUB/SUB DİNLEYİCİSİ ---
async def redis_listener():
    """Tüm worker'lar arka planda bu kanalı dinler. Anons gelirse herkes kendi cache'ini siler."""
    try:
        r = aioredis.from_url(f"redis://{os.getenv('REDIS_HOST', 'redis')}:6379")
        pubsub = r.pubsub()
        await pubsub.subscribe("model_updates")
        print("🎧 Redis Pub/Sub 'model_updates' kanalı dinleniyor...")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                command = message['data'].decode('utf-8')
                if command == "RELOAD_MODELS":
                    model_cache.clear()
                    print("🚨 [MULTI-WORKER SYNC]: Yeni model saptandı. Local RAM Cache temizlendi!")
    except Exception as e:
        print(f"Redis Dinleyici Hatası: {e}")

@app.on_event("startup")
async def startup_event():
    # API ayağa kalkarken arka planda Redis dinleyiciyi başlat
    asyncio.create_task(redis_listener())

class FeaturePayload(BaseModel):
    symbol: str
    volatility: float
    lag_1: float
    lag_3: float
    ma_5: float
    ma_10: float
    momentum: float
    volatility_change: float

def load_model(symbol: str):
    """MLflow'dan Production modelini çeker ve RAM'e yükler"""
    if symbol in model_cache:
        return model_cache[symbol]
    
    model_name = f"model_{symbol}"
    try:
        print(f" MLflow'dan {model_name} (Production) indiriliyor...")
        model_uri = f"models:/{model_name}/Production"
        model = mlflow.sklearn.load_model(model_uri)
        model_cache[symbol] = model
        print(f" {model_name} RAM'e yüklendi!")
        return model
    except Exception as e:
        print(f" Model bulunamadı ({symbol}): {e}")
        return None

@app.post("/predict")
async def predict_price(payload: FeaturePayload):
    """Spark'tan gelen özellikleri alır, anında tahmini döner."""
    model = load_model(payload.symbol)
    
    if not model:
        raise HTTPException(status_code=404, detail=f"{payload.symbol} için Production modeli bulunamadı.")
    
    features_df = pd.DataFrame([{
        "volatility": payload.volatility,
        "lag_1": payload.lag_1,
        "lag_3": payload.lag_3,
        "ma_5": payload.ma_5,
        "ma_10": payload.ma_10,
        "momentum": payload.momentum,
        "volatility_change": payload.volatility_change
    }])
    
    try:
        prediction = model.predict(features_df)[0]
        return {
            "symbol": payload.symbol,
            "predicted_price": round(float(prediction), 5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin hatası: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "loaded_models": list(model_cache.keys())}