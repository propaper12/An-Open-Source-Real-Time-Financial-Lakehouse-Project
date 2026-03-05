import os
import sys
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import shutil
import time
import requests  # Model bitince API'ye "tazele" demek icin ekledim
from deltalake import DeltaTable
from sklearn.metrics import mean_squared_error, r2_score
from mlflow.tracking import MlflowClient

# --- KULLANDIGIM ALGORITMALAR ---
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

os.environ["MLFLOW_DISABLE_LOGGED_MODELS"] = "true"

#1. KONFIGURASYON VE BAGLANTILAR
# MinIO (S3) baglantisini Docker icinden yapmak icin enviroment variable'lari kullaniyorum.
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow_server:5000")
DATA_PATH = "s3://market-data/silver_layer_delta" 

storage_options = {
    "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER", "admin"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
    "AWS_ENDPOINT_URL": MINIO_ENDPOINT,
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    "AWS_ALLOW_HTTP": "true"
}

os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT
os.environ["AWS_ACCESS_KEY_ID"] = storage_options["AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = storage_options["AWS_SECRET_ACCESS_KEY"]

print("Python AutoML Engine baslatiliyor...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("RealTime_AutoML_League")

#2. OZELLIK MUHENDISLIGI (FEATURE ENGINEERING)
def create_smart_features(df):
    """
    Bunu yazmamin sebebi, modelin sadece fiyata degil, trende (MA) ve momentuma
    bakmasini saglamak. Sadece fiyata baksaydi Overfitting olma riski cok yuksekti.
    """
    df = df.sort_values(by="processed_time").reset_index(drop=True)
    df['lag_1'] = df['average_price'].shift(1)
    df['lag_3'] = df['average_price'].shift(3)
    df['ma_5'] = df['average_price'].rolling(window=5).mean()
    df['ma_10'] = df['average_price'].rolling(window=10).mean()
    df['momentum'] = df['average_price'] - df['lag_3']
    df['volatility_change'] = df['volatility'] - df['volatility'].shift(1)
    
    # Modelin tahmin edecegi gercek deger (Bir sonraki adim)
    df['TARGET_PRICE'] = df['average_price'].shift(-1)
    return df.dropna()

#3. VERI CEKME VE MODEL EGITIMI
try:
    print(f"Veri kaynagi taraniyor: {DATA_PATH}")
    # Pandas yerine DeltaLake kutuphanesi kullaniyorum cunku buyuk veride 
    # Parquet okumak CSV okumaktan kat kat daha hizli ve guvenli.
    dt = DeltaTable(DATA_PATH, storage_options=storage_options)
    base_df = dt.to_pandas()
    
    symbol_counts = base_df['symbol'].value_counts()
    target_symbols = symbol_counts[symbol_counts > 20].index.tolist()
    
    if not target_symbols:
        print("Egitim icin yeterli veri seti bulunamadi.")
        sys.exit(0)
        
    for symbol in target_symbols:
        # NESTED RUNS (IC ICE CALISTIRMALAR)
        # Bazi projelerde herkesi tek listeye basiyorlar ama ben UI tarafi 
        # sismesin diye her coine bir "Parent Run" actim.
        with mlflow.start_run(run_name=f"COIN_{symbol}") as parent_run:
            mlflow.log_param("symbol", symbol)
            print(f"\n--- {symbol} Icin Ligi Baslatildi ---")
            
            raw_df = base_df[base_df['symbol'] == symbol].copy()
            feature_df = create_smart_features(raw_df)
            
            feature_cols = ["volatility", "lag_1", "lag_3", "ma_5", "ma_10", "momentum", "volatility_change"]
            X = feature_df[feature_cols]
            y = feature_df["TARGET_PRICE"]
            
            # Zaman serilerinde RandomSplit kullanmak gelecegi gecmise katar (Data Leakage).
            # Bu yuzden veriyi %80 bastan, %20 sondan olacak sekilde duz boldum.
            split_idx = int(len(feature_df) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Aslinda sadece XGBoost da kurabilirdim ama farkli piyasa kosullarinda
            # LightGBM'in daha iyi sonuc verdigini gordum, o yuzden 3'unu yaristiriyorum.
            models = {
                "XGBoost_Pro": XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42, objective='reg:squarederror'),
                "LightGBM_Fast": LGBMRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42, verbose=-1),
                "GradientBoost_Base": GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
            }
            
            best_rmse = float('inf')
            best_model = None
            best_model_name = ""
            
            for name, model in models.items():
                # Her modeli Parent'in altina bir 'Child' olarak kaydediyorum.
                with mlflow.start_run(run_name=name, nested=True) as child_run:
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_test)
                    
                    # MSE de kullanilabilirdi ama RMSE kullanmamdaki amac:
                    # Hata payini direk Dolar/USDT cinsinden gorebilmek.
                    rmse = np.sqrt(mean_squared_error(y_test, predictions))
                    r2 = r2_score(y_test, predictions)
                    
                    mlflow.log_metric("rmse", rmse)
                    mlflow.log_metric("r2", r2)
                    
                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_model = model
                        best_model_name = name

            print(f"Kazanan: {best_model_name} (RMSE: {best_rmse:.5f})")
            
            # Sadece kazanan modeli kaydediyorum, boylece storage sismez.
            mlflow.log_metric("best_rmse", best_rmse)
            mlflow.log_param("winning_algo", best_model_name)

            #MODEL REGISTRY & PRODUCTION
            registered_model_name = f"model_{symbol}"
            temp_path = f"/tmp/model_{symbol}"
            if os.path.exists(temp_path): shutil.rmtree(temp_path)
            
            mlflow.sklearn.save_model(sk_model=best_model, path=temp_path)
            mlflow.log_artifacts(temp_path, artifact_path="model")
            shutil.rmtree(temp_path)
            
            run_id = parent_run.info.run_id
            model_uri = f"runs:/{run_id}/model"
            
            client = MlflowClient()
            try:
                client.create_registered_model(registered_model_name)
            except: pass 

            mv = client.create_model_version(registered_model_name, model_uri, run_id)
            time.sleep(2) 
            
            # Modeli direk "Production" etiketine cekiyorum.
            # Normalde 'Staging' adimi da yapilabilirdi ama bu gercek zamanli bir bot
            # oldugu icin hizi tercih ettim.
            client.transition_model_version_stage(
                name=registered_model_name, 
                version=mv.version,
                stage="Production", 
                archive_existing_versions=True
            )

    #AUTO-RELOAD SİSTEMİ
    print("\nEgitim bitti. Inference API'ye taze model sinyali gonderiliyor...")
    try:
        # FastAPI'ye "modeller egitildi, cache'ini temizle" diyorum.
        requests.post("http://api-gateway:8000/reload", timeout=5)
    except:
        print("Uyari: API reload sinyali gitmedi. Manuel restart gerekebilir.")

except Exception as e:
    print(f"Sistem hatasi: {e}")