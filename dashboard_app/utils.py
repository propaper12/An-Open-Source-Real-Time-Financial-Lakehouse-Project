import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import os

#KONFİGÜRASYON (Environment Variables ile daha güvenli) 
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BUCKET_NAME = "market-data"

# DB Ayarları
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "admin")


@st.cache_resource
def get_s3_fs():
    """
    MinIO S3 Bağlantısını kurar ve önbelleğe alır.
    Sayfa yenilense bile tekrar bağlanmaz, hafızadakini kullanır.
    """
    try:
        fs = s3fs.S3FileSystem(
            key=ACCESS_KEY, 
            secret=SECRET_KEY, 
            client_kwargs={'endpoint_url': MINIO_URL}
        )
        fs.ls(BUCKET_NAME) 
        return fs
    except Exception as e:
        st.error(f" MinIO Bağlantı Hatası: {e}")
        return None

@st.cache_resource
def get_db_conn():
    """
    PostgreSQL Bağlantısını kurar ve önbelleğe alır.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST, 
            database=PG_DB, 
            user=PG_USER, 
            password=PG_PASS, 
            port="5432"
        )
        return conn
    except Exception as e:
        st.error(f" Veritabanı Bağlantı Hatası: {e}")
        return None


@st.cache_data(ttl=60) 
def load_latest_silver_data(limit=10):
    """
    Silver katmanından (MinIO) son işlenen Parquet dosyalarını okur.
    Bu fonksiyonu çağırarak her sayfada kod tekrarından kurtulursun.
    """
    fs = get_s3_fs()
    if not fs: return pd.DataFrame()

    try:
        files = fs.glob(f"s3://{BUCKET_NAME}/silver_layer_delta/**/*.parquet")
        
        if not files:
            return pd.DataFrame()
            
        recent_files = sorted(files)[-limit:] 
        
        dfs = [pd.read_parquet(fs.open(f)) for f in recent_files]
        if dfs:
            df = pd.concat(dfs)
            return df.sort_values('processed_time')
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.warning(f"Veri okuma hatası (Henüz veri oluşmamış olabilir): {e}")

        return pd.DataFrame()
