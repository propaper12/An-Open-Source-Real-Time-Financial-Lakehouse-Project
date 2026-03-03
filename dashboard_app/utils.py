import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import mlflow
import os

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow_server:5000")
MINIO_URL = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
# Şifreleri doğrudan os.getenv ile çekiyoruz, yanına "admin" yazmıyoruz!
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "market-data")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")

# --- 2. GÖRSEL TASARIM (KURUMSAL KİMLİK) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* Binance-Style Dark Theme */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0b0e11; /* Binance Dark BG */
            font-family: 'Inter', sans-serif;
            color: #eaecef;
        }

        /* Hero Section Gradient */
        .hero-section {
            background: linear-gradient(90deg, #1e2329 0%, #0b0e11 100%);
            padding: 40px;
            border-radius: 15px;
            border-left: 5px solid #fcd535; /* Binance Yellow */
            margin-bottom: 25px;
        }

        /* Servis Kartları (Modern & Hover Efektli) */
        [data-testid="stMetric"] {
            background-color: #1e2329;
            border: 1px solid #2b3139;
            border-radius: 10px;
            padding: 15px !important;
            transition: all 0.3s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: #fcd535;
            transform: translateY(-5px);
        }

        /* Kart Konteynerları */
        div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
            background-color: #181a20 !important;
            border: 1px solid #2b3139 !important;
            border-radius: 12px !important;
        }

        /* Butonlar */
        .stButton button {
            background-color: #fcd535 !important;
            color: #0b0e11 !important;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            text-transform: uppercase;
        }
        .stButton button:hover {
            background-color: #d4b12d !important;
            box-shadow: 0px 4px 15px rgba(252, 213, 53, 0.3);
        }

        /* Başlıklar */
        h1, h2, h3 { color: #fcd535 !important; font-weight: 800 !important; }
        
        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #181a20; }
    </style>
    """, unsafe_allow_html=True)
# --- 3. MLFLOW BAĞLANTISI (AKILLI BAĞLANTI) ---
def init_mlflow():
    """
    Burası projenin en kritik noktası. Streamlit Docker içinde çalışırken bazen
    DNS çözümlemesinde sorun yaşayabiliyor.
    Bu yüzden 'Failover' (Hata Toleransı) mekanizması kurdum:
    1. Önce Docker içindeki servis adını (mlflow:5000) dener.
    2. Olmazsa Localhost/Bridge IP'sini dener.
    Böylece bağlantı asla kopmaz.
    """
    primary_uri = MLFLOW_URI
    fallback_uri = "http://host.docker.internal:5000" 
    
    try:
        # Birinci yolu dene
        mlflow.set_tracking_uri(primary_uri)
        client = mlflow.tracking.MlflowClient()
        client.search_experiments() # Test isteği atıyorum
        return True, primary_uri
    except:
        try:
            # Olmadıysa ikinci yolu (Yedek) dene
            mlflow.set_tracking_uri(fallback_uri)
            client = mlflow.tracking.MlflowClient()
            client.search_experiments()
            return True, fallback_uri
        except Exception as e:
            # İkisi de çalışmıyorsa serviste sorun vardır
            return False, str(e)

# --- 4. VERİTABANI & S3 (PERFORMANS İÇİN CACHE) ---
# @st.cache_resource kullanıyorum çünkü her sayfa yenilendiğinde (rerun)
# veritabanına tekrar tekrar bağlanmak sistemi yavaşlatır.
# Bağlantıyı bir kere kurup hafızada tutuyorum.

@st.cache_resource
def get_db_conn():
    try:
        return psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS, port="5432")
    except: return None

@st.cache_resource
def get_s3_fs():
    try:
        return s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY, client_kwargs={'endpoint_url': MINIO_URL})
    except: return None
