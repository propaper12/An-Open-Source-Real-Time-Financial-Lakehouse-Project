import streamlit as st
import s3fs
import psycopg2
import pandas as pd
import mlflow
import os
import time
from datetime import datetime
import graphviz

# --- 1. ENV CONFIG ---
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow_server:5000")
MINIO_URL = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "market-data")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")

# --- 2. PROFESYONEL BINANCE TERMİNAL CSS ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

        .stApp { background-color: #0b0e11; font-family: 'Inter', sans-serif; color: #eaecef; }

        .hero-banner {
            background: linear-gradient(135deg, #1e2329 0%, #0b0e11 100%);
            padding: 40px; border-radius: 20px; border-left: 8px solid #fcd535;
            margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .status-card {
            background-color: #1e2329; border: 1px solid #2b3139; border-radius: 12px;
            padding: 20px; text-align: center; transition: 0.3s;
        }
        .status-card:hover { border-color: #fcd535; transform: translateY(-5px); }

        .led-green { color: #0ecb81; font-weight: bold; }
        .led-red { color: #f6465d; font-weight: bold; }

        h1, h2, h3 { color: #fcd535 !important; font-weight: 800 !important; letter-spacing: -1px; }
        
        .stButton button {
            background-color: #fcd535 !important; color: #0b0e11 !important;
            border-radius: 8px !important; font-weight: 800 !important;
            text-transform: uppercase; padding: 10px 25px !important; width: 100%;
        }

        .arch-container {
            background-color: #181a20; padding: 30px; border-radius: 20px;
            border: 1px solid #2b3139; margin: 20px 0;
        }

        [data-testid="stSidebar"] { background-color: #181a20; border-right: 1px solid #2b3139; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TEKNİK BAĞLANTI KONTROLLERİ ---
@st.cache_resource
def check_connections():
    status = {"Postgres": False, "MinIO": False, "MLflow": False}
    try:
        conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS, port="5432", connect_timeout=1)
        status["Postgres"] = True
        conn.close()
    except: pass
    try:
        fs = s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY, client_kwargs={'endpoint_url': MINIO_URL})
        fs.ls(BUCKET_NAME)
        status["MinIO"] = True
    except: pass
    try:
        mlflow.set_tracking_uri(MLFLOW_URI)
        mlflow.tracking.MlflowClient().search_experiments()
        status["MLflow"] = True
    except: pass
    return status

# --- 4. MİMARİ ŞEMA OLUŞTURUCU (Graphviz) ---
def show_architecture():
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#181a20', color='white', fontname='Inter')
    dot.attr('node', shape='box', style='filled', fontname='Inter', fontcolor='white', color='#2b3139')
    
    # Layer 1: Ingestion
    dot.node('Binance', 'Binance WS\n(Data Source)', fillcolor='#fcd535', fontcolor='black')
    dot.node('Producer', 'Kafka Producer\n(Python)', fillcolor='#474d57')
    dot.node('Kafka', 'Kafka Cluster\n(Message Bus)', fillcolor='#474d57')

    # Layer 2: Processing
    dot.node('SparkSpeed', 'Spark Streaming\n(Speed Layer)', fillcolor='#0052cc')
    dot.node('SparkBatch', 'Batch Processor\n(Rust/Python)', fillcolor='#0052cc')

    # Layer 3: Storage
    dot.node('MinIO', 'MinIO (S3)\n(Delta Lakehouse)', fillcolor='#0ecb81')
    dot.node('Postgres', 'TimescaleDB\n(Serving DB)', fillcolor='#0ecb81')

    # Layer 4: ML & App
    dot.node('MLflow', 'MLflow\n(Model Registry)', fillcolor='#9b59b6')
    dot.node('Inference', 'FastAPI\n(Inference MaaS)', fillcolor='#9b59b6')
    dot.node('UI', 'Streamlit Terminal\n(Serving Layer)', fillcolor='#f6465d')

    # Bağlantılar
    dot.edge('Binance', 'Producer')
    dot.edge('Producer', 'Kafka')
    dot.edge('Kafka', 'SparkSpeed')
    dot.edge('SparkSpeed', 'Inference', label='Predict Request')
    dot.edge('Inference', 'SparkSpeed', label='Response')
    dot.edge('SparkSpeed', 'Postgres', label='Real-time Write')
    dot.edge('SparkSpeed', 'MinIO', label='Silver Write')
    dot.edge('SparkBatch', 'MinIO', label='Historical Load')
    dot.edge('MinIO', 'MLflow', label='Training Data')
    dot.edge('MLflow', 'Inference', label='Model Load')
    dot.edge('Postgres', 'UI', label='Slow Path Query')
    dot.edge('Kafka', 'UI', label='Fast Path Tick')

    st.graphviz_chart(dot)

# --- 5. ANA SAYFA İÇERİĞİ ---
def main():
    inject_custom_css()
    
    # Hero Section
    st.markdown(f"""
    <div class="hero-banner">
        <p style="color: #fcd535; font-weight: 700; text-transform: uppercase; margin-bottom: 10px;">V2.1 - Enterprise Lakehouse Architecture</p>
        <h1>UÇTAN UCA FİNANSAL<br>VERİ EKOSİSTEMİ</h1>
        <p style="font-size: 18px; color: #848e9c;">
            Bu platform; <b>Binance</b> üzerinden akan saniyelik verileri <b>Lambda Mimarisi</b> ile işleyen, 
            <b>Delta Lake</b> üzerinde depolayan ve <b>MLOps</b> prensipleriyle tahminleyen profesyonel bir veri terminalidir.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Mimari Şema Bölümü (KRİTİK GÖRSEL)
    st.subheader("🏗️ Sistem Akış Şeması (End-to-End Pipeline)")
    with st.container():
        st.markdown('<div class="arch-container">', unsafe_allow_html=True)
        show_architecture()
        st.markdown('</div>', unsafe_allow_html=True)

    # Sistem Durum Paneli
    st.subheader("🌐 Canlı Altyapı Metrikleri")
    conn_status = check_connections()
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div class="status-card"><p style="color:#848e9c;">TimescaleDB</p><h3>Postgres</h3>
            <span class="{'led-green' if conn_status['Postgres'] else 'led-red'}">{'● ONLINE' if conn_status['Postgres'] else '○ OFFLINE'}</span></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="status-card"><p style="color:#848e9c;">Object Storage</p><h3>MinIO (S3)</h3>
            <span class="{'led-green' if conn_status['MinIO'] else 'led-red'}">{'● ONLINE' if conn_status['MinIO'] else '○ OFFLINE'}</span></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="status-card"><p style="color:#848e9c;">ML Engine</p><h3>MLflow</h3>
            <span class="{'led-green' if conn_status['MLflow'] else 'led-red'}">{'● ONLINE' if conn_status['MLflow'] else '○ OFFLINE'}</span></div>""", unsafe_allow_html=True)

    st.divider()

    # Navigasyon
    st.subheader("🚀 Hızlı Erişim")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.info("### ⚡ Real-Time\nKafka & Spark Dual-Track yoluyla milisaniyelik analiz.")
        if st.button("CANLI TERMİNAL"): st.switch_page("pages/_Canli_Piyasa.py")
    with m2:
        st.success("### 📂 Lakehouse\nDelta Lake ve Rust motoruyla 10 yıllık borsa arşivi.")
        if st.button("GEÇMİŞ ANALİZ"): st.switch_page("pages/Gecmis_Analiz.py")
    with m3:
        st.warning("### 🧠 MLOps\nAutoML Liderlik Tablosu ve Model Versiyonlama.")
        if st.button("MLOPS MERKEZİ"): st.switch_page("pages/_MLOps_Center.py")

    st.divider()
    
    # Terminal Log Footer
    st.markdown(f"""
    <div style="background-color: #181a20; padding: 20px; border-radius: 10px; border: 1px solid #2b3139; font-family: 'JetBrains Mono'; font-size: 13px;">
        <p style="color: #848e9c;">> _Initialization_Sequence_Complete...</p>
        <p style="color: #0ecb81;">- Lambda Architecture: ACTIVE (Speed & Batch Layers)</p>
        <p style="color: #0ecb81;">- MaaS Engine: OPERATIONAL (FastAPI)</p>
        <p style="color: #0ecb81;">- Storage Layer: DELTA LAKE ENABLED (MinIO)</p>
        <p style="color: #fcd535;">- Last Heartbeat: {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()