import yfinance as yf
import pandas as pd
import os
from deltalake.writer import write_deltalake

# --- DOCKER İÇİ MINIO BAĞLANTISI ---
storage_options = {
    "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER", "admin"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
    "AWS_ENDPOINT_URL": os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    "AWS_ALLOW_HTTP": "true"
}

# TOP 25 COIN LISTESI
COINS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", 
    "ADA-USD", "AVAX-USD", "DOGE-USD", "DOT-USD", "LINK-USD",
    "TRX-USD", "SHIB-USD", "LTC-USD", "UNI-USD", "BCH-USD",
    "ATOM-USD", "XLM-USD", "NEAR-USD", "ALGO-USD", "VET-USD",
    "FIL-USD", "ICP-USD", "SAND-USD", "MANA-USD", "FTM-USD"
]

def fetch_and_save_data(interval, period, target_path):
    print(f"\nETL BASLATILDI: {interval} | {period} -> {target_path}")
    all_data = []
    
    for coin in COINS:
        print(f"{coin} cekiliyor...")
        try:
            ticker = yf.Ticker(coin)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty: continue
                
            df = df.reset_index()
            date_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
            
            df_clean = pd.DataFrame({
                'timestamp': pd.to_datetime(df[date_col], utc=True),
                'symbol': coin.replace('-USD', 'USDT'),
                'open': df['Open'].astype(float),
                'high': df['High'].astype(float),
                'low': df['Low'].astype(float),
                'close': df['Close'].astype(float),
                'volume': df['Volume'].astype(float)
            })
            
            df_clean['year'] = df_clean['timestamp'].dt.year # Partitioning icin
            all_data.append(df_clean)
            
        except Exception as e:
            print(f"Hata ({coin}): {e}")
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"{len(final_df)} satir veri Delta Lake'e (MinIO) yaziliyor...")
        
        write_deltalake(
            target_path, 
            final_df, 
            mode="overwrite", 
            partition_by=["symbol", "year"], 
            storage_options=storage_options
        )
        print(f"🎉 {interval} Islemi Basarili!")

if __name__ == "__main__":
    # 1. 5 Dakikalik (Scalping - Maks 60 Gun)
    fetch_and_save_data("5m", "60d", "s3://market-data/historical_5m_delta")
    
    # 2. 15 Dakikalik (Day Trading - Maks 60 Gun)
    fetch_and_save_data("15m", "60d", "s3://market-data/historical_15m_delta")
    
    # 3. Saatlik (Swing - Maks 730 Gun)
    fetch_and_save_data("1h", "730d", "s3://market-data/historical_hourly_delta")
    
    # 4. Gunluk (Long Term - 10 Yil)
    fetch_and_save_data("1d", "10y", "s3://market-data/historical_daily_delta")