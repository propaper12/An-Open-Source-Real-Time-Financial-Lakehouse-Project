import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import mlflow
import os

# --- 1. KONFİGÜRASYON VE GÜVENLİK ---
# Şifreleri ve adresleri kodun içine gömmek yerine (hardcoded), ortam değişkenlerinden çekiyorum.
# Bu sayede proje Docker'da da çalışsa, Local'de de çalışsa ayar değiştirmeme gerek kalmıyor.
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BUCKET_NAME = "market-data"
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "admin")

# --- 2. GÖRSEL TASARIM (KURUMSAL KİMLİK) ---
def inject_custom_css():
    """
    Standart Streamlit arayüzü çok basit kaldığı için, DataRobot/B2Metric tarzı
    profesyonel bir 'Dark Mode' (Karanlık Tema) tasarladım.
    Burada CSS ile arayüzün renklerini, kart yapılarını ve fontlarını manipüle ediyorum.
    """
    st.markdown("""
    <style>
        /* --- RENK PALETİ (SİYAH & YEŞİL VURGULU) --- */
        :root {
            --bg-color: #0E1117;       /* Göz yormayan mat siyah arka plan */
            --card-color: #262730;     /* Kartlar için koyu gri */
            --border-color: #41444C;   /* İnce gri çerçeveler */
            --accent-color: #FF4B4B;   /* Streamlit kırmızısı (Vurgular için) */
            --text-color: #FAFAFA;     /* Okunabilir beyaz metin */
            --success-color: #00CC96;  /* Başarılı durumlar için yeşil */
        }
        
        /* Sayfanın genel arka planını değiştiriyorum */
        .stApp {
            background-color: var(--bg-color);
        }
        
        /* Sol menüyü (Sidebar) tamamen siyah yapıp ayrıştırıyorum */
        [data-testid="stSidebar"] {
            background-color: #000000; 
            border-right: 1px solid var(--border-color);
        }

        /* Grafikleri ve metrikleri içine koyduğum 'Kart' yapısı */
        [data-testid="stContainer"] {
            background-color: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
        }
        
        /* Metriklerin daha şık görünmesi için renk ayarları */
        .stMetricLabel { color: #B0B3B8 !important; }
        .stMetricValue { color: var(--text-color) !important; }
        
        /* Tablo kenarlıklarını temaya uyduruyorum */
        [data-testid="stDataFrame"] { border: 1px solid var(--border-color); }
        
        /* Başlıkların her zaman beyaz kalmasını sağlıyorum */
        h1, h2, h3 { color: var(--text-color) !important; }
        
        /* Butonlara hover (üzerine gelince) efekti ekledim */
        .stButton button {
            background-color: #31333F;
            color: white;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }
        
        a { color: var(--accent-color) !important; }

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