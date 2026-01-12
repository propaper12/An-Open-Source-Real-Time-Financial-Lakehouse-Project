import streamlit as st
import pandas as pd
import s3fs
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psutil
import docker
import psycopg2
import os
import numpy as np
from datetime import datetime

MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000") 
MINIO_CONSOLE_URL = "http://localhost:9001"
MLFLOW_URL = "http://localhost:5000"
AIRFLOW_URL = "http://localhost:8081"
ACCESS_KEY = "admin"
SECRET_KEY = "admin12345"
BUCKET_NAME = "market-data"
SILVER_PATH = "silver_layer_delta"

st.set_page_config(page_title="Ultimate DataFlow Terminal", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e1e4e8; }
    .metric-card { 
        background-color: #161b22; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        text-align: center;
    }
    .status-online { color: #238636; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_db_conn():
    return psycopg2.connect(host="postgres", database="market_db", user="admin", password="admin", port="5432")

def get_s3_fs():
    return s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY, client_kwargs={'endpoint_url': MINIO_URL})

def add_indicators(df):
    if len(df) < 20: return df
    delta = df['average_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['MA20'] = df['average_price'].rolling(window=20).mean()
    df['std'] = df['average_price'].rolling(window=20).std()
    df['Upper'] = df['MA20'] + (df['std'] * 2)
    df['Lower'] = df['MA20'] - (df['std'] * 2)
    return df

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8297/8297332.png", width=80)
    st.title("Admin Ops Center")
    
    st.markdown("### 🔗 Hızlı Linkler")
    st.markdown(f"📂 [MinIO Console (9001)]({MINIO_CONSOLE_URL})")
    st.markdown(f"🧠 [MLflow Tracking (5000)]({MLFLOW_URL})")
    st.markdown(f"⚙️ [Airflow DAGs (8081)]({AIRFLOW_URL})")
    
    st.markdown("---")
    st.subheader("🛠️ Pipeline Manuel Tetikleme")
    if st.button("🚀 Spark ML Eğitimi Başlat"):
        os.system("docker exec spark-silver python train_model.py &")
        st.toast("MLflow Run Başlatıldı!")
    
    if st.button("💎 dbt Gold Refresh"):
        os.system("docker exec dbt_transformer dbt run &")
        st.toast("PostgreSQL Tabloları Güncelleniyor...")

st.title("🚀 Enterprise MLOps & Real-Time Lakehouse")

try:
    fs = get_s3_fs()
    files = fs.glob(f"s3://{BUCKET_NAME}/{SILVER_PATH}/**/*.parquet")
    df_raw = pd.concat([pd.read_parquet(fs.open(f)) for f in sorted(files)[-40:]])
    df_raw['processed_time'] = pd.to_datetime(df_raw['processed_time']) + pd.Timedelta(hours=3)
    df = add_indicators(df_raw.sort_values('processed_time'))
except:
    st.error("MinIO veya Spark verisi bulunamadı. Lütfen sistemleri başlatın.")
    st.stop()

tab_realtime, tab_mlops, tab_gold, tab_infra = st.tabs([
    "📈 Canlı Market & Teknik Analiz", "🤖 MLflow & Model Performansı", "🏆 dbt Gold Layer", "📟 Sistem Mimarisi & Sağlık"
])

with tab_realtime:
    selected_sym = st.selectbox("Sembol Seçin", df['symbol'].unique())
    df_sub = df[df['symbol'] == selected_sym].tail(100)
    last = df_sub.iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Anlık Fiyat", f"${last['average_price']:,.2f}", f"{last['average_price']-df_sub.iloc[-2]['average_price']:.2f}")
    with c2: st.metric("AI Tahmini", f"${last['predicted_price']:,.2f}")
    with c3: st.metric("RSI (14)", f"{last.get('RSI', 0):.2f}")
    with c4: st.metric("Volatilite (Spark)", f"{last['volatility']:.6f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sub['processed_time'], y=df_sub['Upper'], name="Bollinger Üst", line=dict(color='rgba(255,255,255,0.1)')))
    fig.add_trace(go.Scatter(x=df_sub['processed_time'], y=df_sub['Lower'], name="Bollinger Alt", fill='tonexty', line=dict(color='rgba(255,255,255,0.1)')))
    fig.add_trace(go.Scatter(x=df_sub['processed_time'], y=df_sub['average_price'], name="Piyasa", line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(x=df_sub['processed_time'], y=df_sub['predicted_price'], name="AI Tahmin", line=dict(dash='dot', color='#ff7f0e')))
    fig.update_layout(height=600, template="plotly_dark", title=f"{selected_sym} Detaylı AI Analizi")
    st.plotly_chart(fig, use_container_width=True)

with tab_mlops:
    st.subheader("🤖 MLflow Model Tracking & Accuracy")
    df['Error'] = (df['average_price'] - df['predicted_price']).abs()
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("#### Tahmin Doğruluğu (Regression Plot)")
        fig_acc = px.scatter(df, x="average_price", y="predicted_price", color="Error", trendline="ols")
        st.plotly_chart(fig_acc, use_container_width=True)
    with col_b:
        st.write("#### Hata Dağılımı (Residual Analysis)")
        fig_err = px.histogram(df, x="Error", nbins=30, title="MAE Distribution")
        st.plotly_chart(fig_err, use_container_width=True)

with tab_gold:
    st.subheader("🏆 dbt Analytics - PostgreSQL Gold Katmanı")
    try:
        conn = get_db_conn()
        df_perf = pd.read_sql("SELECT * FROM fct_model_performance ORDER BY observation_hour DESC LIMIT 10", conn)
        df_summary = pd.read_sql("SELECT * FROM gold_market_summary LIMIT 10", conn)
        
        st.write("#### 📊 Saatlik Performans (dbt fct_model_performance)")
        st.dataframe(df_perf, use_container_width=True)
        
        st.write("#### 💰 Market Özeti (dbt gold_market_summary)")
        st.table(df_summary)
        conn.close()
    except:
        st.warning("dbt tabloları yükleniyor... Lütfen Airflow üzerinden dbt job'ını kontrol edin.")

with tab_infra:
    st.subheader("📟 Uçtan Uca Boru Hattı İzleme")
    
    i1, i2, i3 = st.columns(3)
    i1.metric("Sunucu CPU", f"%{psutil.cpu_percent()}")
    i2.metric("Sunucu RAM", f"%{psutil.virtual_memory().percent}")
    
    try:
        client = docker.from_env()
        containers = client.containers.list()
        i3.metric("Aktif Konteynerler", len(containers))
        
        st.write("#### 🐋 Docker Pipeline Durumu")
        c_data = [{"Servis": c.name, "Durum": c.status, "İmaj": c.image.tags[0] if c.image.tags else "N/A"} for c in containers]
        st.table(c_data)
    except:
        st.error("Docker Socket erişimi yok!")

time.sleep(10)
st.rerun()
