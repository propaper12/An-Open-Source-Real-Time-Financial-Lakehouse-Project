import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import os

#KONFİGÜRASYON
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BUCKET_NAME = "market-data"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "admin")

#STİL FONKSİYONU
def inject_custom_css():
    """
    Bu fonksiyon çağrıldığında sayfaya DataRobot/Enterprise stili CSS enjekte eder.
    Tüm sayfalarda en başta çağırılmalıdır.
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
        
        /* Kart Görünümü (st.container border=True olanlar) */
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
        
        /* Butonlar - DataRobot Mavisi */
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

#BAĞLANTI FONKSİYONLARI
@st.cache_resource
def get_s3_fs():
    try:
        fs = s3fs.S3FileSystem(
            key=ACCESS_KEY, 
            secret=SECRET_KEY, 
            client_kwargs={'endpoint_url': MINIO_URL}
        )
        return fs
    except Exception as e:
        st.error(f" MinIO Bağlantı Hatası: {e}")
        return None

@st.cache_resource
def get_db_conn():
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
        st.error(f"Veritabanı Bağlantı Hatası: {e}")
        return None

@st.cache_data(ttl=60) 
def load_latest_silver_data(limit=10):
    fs = get_s3_fs()
    if not fs: return pd.DataFrame()

    try:
        files = fs.glob(f"s3://{BUCKET_NAME}/silver_layer_delta/**/*.parquet")
        if not files: return pd.DataFrame()
            
        recent_files = sorted(files)[-limit:] 
        dfs = [pd.read_parquet(fs.open(f)) for f in recent_files]
        
        if dfs:
            df = pd.concat(dfs)
            return df.sort_values('processed_time')
        else:
            return pd.DataFrame()
            
    except Exception as e:
        return pd.DataFrame()