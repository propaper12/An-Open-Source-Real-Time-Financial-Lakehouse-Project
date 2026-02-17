import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import os

# --- KONFİGÜRASYON (Environment Variables) ---
# Docker ortamında servis isimlerini (minio, postgres) kullanır.
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BUCKET_NAME = "market-data"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "admin")

# --- STİL FONKSİYONU (CSS) ---
def inject_custom_css():
    """
    Sayfaya Enterprise/DataRobot stili CSS enjekte eder.
    """
    st.markdown("""
    <style>
        /* Ana Arka Plan */
        .stApp {
            background-color: #0E1117;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #16181C;
            border-right: 1px solid #303339;
        }
        
        /* Kart Görünümü */
        [data-testid="stContainer"] {
            background-color: #1E2127;
            border: 1px solid #303339;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        /* Metrikler ve Başlıklar */
        h1, h2, h3 {
            color: #FAFAFA !important;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 600;
        }
        
        /* Butonlar */
        .stButton button {
            background-color: #262730;
            color: #00ADB5;
            border: 1px solid #00ADB5;
            border-radius: 4px;
            font-weight: bold;
        }
        .stButton button:hover {
            background-color: #00ADB5;
            color: white;
            border-color: #00ADB5;
        }
        
        /* Link Butonları */
        a[kind="primary"] {
            background-color: #00ADB5 !important;
            color: white !important;
            border: none;
        }

        /* Divider Rengi */
        hr {
            border-color: #303339;
        }
    </style>
    """, unsafe_allow_html=True)

# --- BAĞLANTI FONKSİYONLARI ---

@st.cache_resource
def get_s3_fs():
    """
    MinIO (S3) dosya sistemi bağlantısı.
    Stateless olduğu için cache kullanmak güvenlidir ve performansı artırır.
    """
    try:
        fs = s3fs.S3FileSystem(
            key=ACCESS_KEY, 
            secret=SECRET_KEY, 
            client_kwargs={'endpoint_url': MINIO_URL}
        )
        return fs
    except Exception as e:
        st.error(f"❌ MinIO Bağlantı Hatası: {e}")
        return None

def get_db_conn():
    """
    PostgreSQL veritabanı bağlantısı.
    ÖNEMLİ: Burada @st.cache_resource KULLANMIYORUZ.
    Cache kullanılırsa, bağlantı zaman aşımına uğradığında 'connection already closed' hatası alınır.
    Her çağrıda taze bağlantı açmak en güvenli yöntemdir.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST, 
            database=PG_DB, 
            user=PG_USER, 
            password=PG_PASS, 
            port="5432",
            connect_timeout=3  # Bağlantı 3 sn içinde kurulamazsa hata ver (UI donmasın)
        )
        return conn
    except Exception as e:
        # Hata detayını terminale bas, UI'da temiz bir uyarı gösterilebilir
        print(f"❌ DB Bağlantı Hatası: {e}")
        return None

@st.cache_data(ttl=60) 
def load_latest_silver_data(limit=10):
    """
    Delta Lake'ten son işlenen verileri okur.
    Her 60 saniyede bir önbelleği yeniler (TTL).
    """
    fs = get_s3_fs()
    if not fs: return pd.DataFrame()

    try:
        # MinIO üzerindeki parquet dosyalarını bul
        files = fs.glob(f"s3://{BUCKET_NAME}/silver_layer_delta/**/*.parquet")
        if not files: return pd.DataFrame()
            
        # En son eklenen dosyaları al
        recent_files = sorted(files)[-limit:] 
        
        # Dosyaları oku ve birleştir
        dfs = [pd.read_parquet(fs.open(f)) for f in recent_files]
        
        if dfs:
            df = pd.concat(dfs)
            return df.sort_values('processed_time')
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Data Load Error: {e}")
        return pd.DataFrame()