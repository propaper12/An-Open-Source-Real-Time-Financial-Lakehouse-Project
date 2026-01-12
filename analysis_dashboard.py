import streamlit as st
import pandas as pd
import s3fs
import time
import plotly.express as px
import plotly.graph_objects as go
import uuid
import numpy as np
import random
import psutil
import subprocess
import os
import docker
from datetime import datetime, timedelta

# --- BAĞLANTILAR VE AYARLAR ---
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

MINIO_URL = os.getenv("MINIO_URL", "http://localhost:9000")
ACCESS_KEY = "admin"
SECRET_KEY = "admin12345"
BUCKET_NAME = "market-data"
SILVER_PATH = "silver_layer_delta"
MODEL_METRICS_PATH = "model_metrics_delta"
IMPORTANCE_PATH = "feature_importance_delta"
CATALOG_PATH = "data_catalog_delta"
TIMEZONE_OFFSET = 3

st.set_page_config(page_title="OpenDataFlow - Architecture", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    .stMetric { background-color: #FFFFFF !important; border: 1px solid #D1D5DB; padding: 15px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800; font-size: 24px; }
    .stDataFrame { border: 1px solid #D1D5DB; background-color: white; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

fs = s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY, client_kwargs={'endpoint_url': MINIO_URL}, use_listings_cache=False)
docker_client = docker.from_env()

# --- YARDIMCI FONKSİYONLAR ---

def get_real_container_logs():
    logs = []
    targets = ['producer', 'spark-silver', 'kafka', 'dbt_transformer', 'api_gateway']
    for t in targets:
        try:
            container = docker_client.containers.get(t)
            if container.status == 'running':
                raw = container.logs(tail=5).decode('utf-8').strip().split('\n')
                for line in raw:
                    if line:
                        logs.append({"ts": datetime.now().strftime('%H:%M:%S'), "level": "INFO", "comp": t.upper(), "msg": line[:100]})
        except: continue
    return logs

def get_system_metrics():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    try:
        active_containers = len(docker_client.containers.list())
    except: active_containers = 0
    return cpu, mem, active_containers

def emergency_stop_system():
    try:
        containers = docker_client.containers.list()
        for c in containers:
            if "dashboard" not in c.name: c.stop()
        return True, "Sistem Güvenle Durduruldu."
    except Exception as e: return False, str(e)

def trigger_training_process():
    try:
        container = docker_client.containers.get('spark-silver')
        # Arka planda tetikle
        container.exec_run("python train_model.py", detach=True)
        return True, "Eğitim Başlatıldı (Background)", ""
    except Exception as e: return False, "", str(e)

def run_dbt_job():
    try:
        container = docker_client.containers.get('dbt_transformer')
        exec_log = container.exec_run("dbt run") 
        return True, exec_log.output.decode("utf-8")
    except Exception as e: return False, str(e)

def enrich_data_with_indicators(df):
    if df.empty: return df
    window = 14
    delta = df['average_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['SMA_20'] = df['average_price'].rolling(window=20).mean()
    df['Bollinger_Upper'] = df['SMA_20'] + (df['average_price'].rolling(window=20).std() * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (df['average_price'].rolling(window=20).std() * 2)
    df['MACD'] = df['average_price'].ewm(span=12).mean() - df['average_price'].ewm(span=26).mean()
    df['Signal_Line'] = df['MACD'].ewm(span=9).mean()
    df['Diff'] = df['average_price'] - df['predicted_price']
    return df

def get_feature_importance():
    try:
        all_files = fs.glob(f"s3://{BUCKET_NAME}/{IMPORTANCE_PATH}/**/*.parquet")
        data_files = [f for f in all_files if "part-" in f]
        if not data_files: return pd.DataFrame()
        dfs = [pd.read_parquet(fs.open(f)) for f in data_files]
        return pd.concat(dfs, ignore_index=True).sort_values("importance", ascending=False)
    except: return pd.DataFrame()

def get_all_models_metrics():
    try:
        all_files = fs.glob(f"s3://{BUCKET_NAME}/{MODEL_METRICS_PATH}/**/*.parquet")
        data_files = [f for f in all_files if "part-" in f]
        if not data_files: return pd.DataFrame()
        dfs = [pd.read_parquet(fs.open(f)) for f in data_files[-40:]]
        metrics_df = pd.concat(dfs, ignore_index=True)
        
        # Algoritma adını temizleme (Örn: path/to/BTC_RandomForest... -> RandomForest)
        def clean_algo_name(name):
            if "RandomForest" in name: return "Random Forest"
            if "LinearRegression" in name: return "Linear Regression"
            if "GBT" in name: return "Gradient Boosted Trees"
            if "DecisionTree" in name: return "Decision Tree"
            return name
            
        metrics_df['Algorithm'] = metrics_df['model_name'].apply(clean_algo_name)
        metrics_df['training_time'] = pd.to_datetime(metrics_df['training_time']) + pd.Timedelta(hours=TIMEZONE_OFFSET)
        return metrics_df.sort_values('r2', ascending=False)
    except: return pd.DataFrame()

def get_all_data():
    try:
        all_files = fs.glob(f"s3://{BUCKET_NAME}/{SILVER_PATH}/**/*.parquet")
        data_files = [f for f in all_files if "part-" in f]
        if not data_files: return pd.DataFrame(), 0, None
        # Son 150 dosya
        dfs = [pd.read_parquet(fs.open(f)) for f in data_files[-150:]]
        df = pd.concat(dfs, ignore_index=True)
        df['processed_time'] = pd.to_datetime(df['processed_time']) + pd.Timedelta(hours=TIMEZONE_OFFSET)
        df = df.sort_values('processed_time').drop_duplicates(subset=['processed_time', 'symbol'], keep='last')
        return df, len(data_files), df['processed_time'].max()
    except: return pd.DataFrame(), 0, None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8297/8297332.png", width=60)
    st.header("Financial Lakehouse")
    
    st.markdown("### ⚙️ Operasyonlar")
    if st.button("🚀 Modeli Yeniden Eğit"):
        success, out, err = trigger_training_process()
        if success: st.success(out)
        else: st.error(err)
        
    if st.button("📊 Raporları Güncelle (dbt)"):
        suc, log = run_dbt_job()
        if suc: st.toast("Raporlar Gold Katmanına Yazıldı!")
        
    if st.button("🛑 SİSTEMİ DURDUR", type="primary"):
        success, msg = emergency_stop_system()
        if success: st.error(msg)

    refresh_rate = st.slider("Canlı Veri Hızı (sn)", 1, 60, 5)
    
    st.markdown("---")
    df_raw, total_files, last_time = get_all_data()
    st.metric("📦 Delta Dosyası", total_files)
    st.caption(f"Son Güncelleme: {last_time}")

# --- ANA EKRAN ---
st.title("🚀 Real-Time Financial Lakehouse & AI Platform")
st.markdown("*Big Data, Streaming & Machine Learning Architecture*")

# Sekme İsimleri Güncellendi
tab_live, tab_auto, tab_cat, tab_self, tab_logs, tab_sql = st.tabs([
    "📈 Canlı Borsa & AI", 
    "🤖 Model Laboratuvarı", 
    "🏗️ Mimari & Teknoloji", 
    "🛠️ Self-Service BI", 
    "📟 Sistem Logları", 
    "💾 SQL Workbench"
])

# --- TAB 1: LIVE DATA ---
if not df_raw.empty:
    selected_sym = st.sidebar.selectbox("Varlık Seç", df_raw['symbol'].unique())
    selected_df = enrich_data_with_indicators(df_raw[df_raw['symbol'] == selected_sym].copy())
    
    if not selected_df.empty:
        last = selected_df.iloc[-1]
        
        with tab_live:
            # KPI Kartları
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(f"{selected_sym} Fiyat", f"${last['average_price']:,.2f}", delta=None)
            
            signal = "AL 🟢" if last['predicted_price'] > last['average_price'] else "SAT 🔴"
            k2.metric("AI Sinyali", signal)
            
            dev = last['predicted_price'] - last['average_price']
            k3.metric("AI Tahmin Hedefi", f"${last['predicted_price']:,.2f}", delta=f"{dev:.2f}")
            
            k4.metric("Volatilite (Risk)", f"{last.get('volatility', 0):.4f}")

        
            col_main, col_side = st.columns([3, 1])
            with col_main:
                st.subheader("Fiyat Hareketi ve AI Tahmin Bandı")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=selected_df['processed_time'], y=selected_df['Bollinger_Upper'], line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=selected_df['processed_time'], y=selected_df['Bollinger_Lower'], fill='tonexty', fillcolor='rgba(173, 216, 230, 0.2)', line=dict(width=0), name='Bollinger Band'))
                fig.add_trace(go.Scatter(x=selected_df['processed_time'], y=selected_df['average_price'], name='Gerçek Fiyat', line=dict(color='#2563EB', width=2)))
                fig.add_trace(go.Scatter(x=selected_df['processed_time'], y=selected_df['predicted_price'], name='Yapay Zeka Tahmini', line=dict(dash='dot', color='#F59E0B', width=2)))
                
                fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig, use_container_width=True)

            with col_side:
                st.subheader("Teknik Göstergeler")
                st.plotly_chart(px.line(selected_df, x='processed_time', y='RSI', title="RSI (Momentum)"), use_container_width=True)
                st.plotly_chart(px.bar(selected_df.tail(20), x='processed_time', y='Diff', title="AI Hata Payı", color='Diff'), use_container_width=True)

with tab_auto:
    st.markdown("### 🤖 Makine Öğrenmesi Modelleri ve Performans Analizi")
    st.caption("Bu panel, Spark ML ile eğitilen farklı algoritmaların (Random Forest, Linear Regression, GBT) gerçek zamanlı başarı oranlarını kıyaslar.")
    
    models_df = get_all_models_metrics()
    
    if not models_df.empty:
        m1, m2 = st.columns([2, 1])
        
        with m1:
            st.markdown("##### 🏆 Algoritma Liderlik Tablosu (R2 Score)")
            fig_perf = px.bar(
                models_df.head(10), 
                x="r2", 
                y="Algorithm", 
                color="Algorithm",
                orientation='h',
                title="Hangi Model Daha Başarılı?",
                text_auto='.3f',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_perf.update_layout(showlegend=False)
            st.plotly_chart(fig_perf, use_container_width=True)
            
        with m2:
            st.markdown("##### 📉 Hata Oranları (RMSE)")
            # RMSE Karşılaştırması
            fig_err = px.scatter(
                models_df, 
                x="training_time", 
                y="rmse", 
                color="Algorithm",
                size="r2",
                title="Zaman İçinde Hata Değişimi"
            )
            st.plotly_chart(fig_err, use_container_width=True)

        st.markdown("#### 🔍 Detaylı Model Metrikleri")
        st.dataframe(
            models_df[['Algorithm', 'model_name', 'r2', 'rmse', 'mae', 'training_time']], 
            use_container_width=True,
            hide_index=True
        )
        
        imp_df = get_feature_importance()
        if not imp_df.empty:
             st.markdown("####  Öznitelik Önemi (Feature Importance)")
             st.plotly_chart(px.bar(imp_df, x='importance', y='feature', orientation='h'), use_container_width=True)
    else:
        st.info("Henüz model metriği üretilmedi. Lütfen 'Modeli Yeniden Eğit' butonuna basın.")

with tab_cat:
    st.markdown("### 🏗️ Uçtan Uca Veri Mimarisi (End-to-End Architecture)")
    st.caption("Projede kullanılan Modern Data Stack (MDS) teknolojilerinin akış diyagramı.")

    if GRAPHVIZ_AVAILABLE:
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR', fontsize='12', bgcolor='transparent')
        
        graph.attr('node', shape='box', style='filled', fillcolor='white', color='#333333', fontname='Helvetica')
        graph.attr('edge', color='#666666', arrowsize='0.8')

        with graph.subgraph(name='cluster_source') as c:
            c.attr(label='1. Veri Kaynakları', color='blue', style='dashed')
            c.node('BINANCE', 'Binance WebSocket\n(Live Crypto)', shape='ellipse', fillcolor='#F3BA2F')
            c.node('API', 'REST API\n(HTTP POST)', shape='ellipse', fillcolor='#85EA2D')

        with graph.subgraph(name='cluster_ingest') as c:
            c.attr(label='2. Ingestion Layer', color='orange')
            c.node('API_GW', 'FastAPI Gateway\n(Python)', shape='component')
            c.node('KAFKA', 'Apache Kafka\n(Message Broker)', shape='box3d', fillcolor='#E0E0E0')
        
        with graph.subgraph(name='cluster_process') as c:
            c.attr(label='3. Processing & ML', color='green')
            c.node('SPARK_STREAM', 'Spark Streaming\n(Consumer)', shape='component', fillcolor='#E25A1C', fontcolor='white')
            c.node('SPARK_ML', 'Spark MLlib\n(Training & Inference)', shape='component', fillcolor='#E25A1C', fontcolor='white')

        with graph.subgraph(name='cluster_storage') as c:
            c.attr(label='4. Storage Layer (Lakehouse)', color='purple')
            c.node('MINIO', 'MinIO (S3)\nDelta Lake Tables', shape='cylinder', fillcolor='#C72C48', fontcolor='white')
            c.node('POSTGRES', 'PostgreSQL\n(Serving Layer)', shape='cylinder', fillcolor='#336791', fontcolor='white')

        with graph.subgraph(name='cluster_viz') as c:
            c.attr(label='5. Serving & BI', color='red')
            c.node('STREAMLIT', 'Streamlit Dashboard\n(This App)', shape='folder', fillcolor='#FF4B4B', fontcolor='white')
            c.node('DBT', 'dbt\n(Transformation)', shape='note')

        # Bağlantılar
        graph.edge('BINANCE', 'KAFKA', label=' JSON')
        graph.edge('API', 'API_GW')
        graph.edge('API_GW', 'KAFKA')
        graph.edge('KAFKA', 'SPARK_STREAM', label=' Topics')
        graph.edge('SPARK_STREAM', 'MINIO', label=' Bronze/Silver (Delta)')
        graph.edge('MINIO', 'SPARK_ML', label=' Historical Data')
        graph.edge('SPARK_ML', 'POSTGRES', label=' JDBC Write')
        graph.edge('POSTGRES', 'STREAMLIT', label=' SQL Query')
        graph.edge('POSTGRES', 'DBT', label=' T')
        
        st.graphviz_chart(graph, use_container_width=True)
    else:
        st.warning("Graphviz kütüphanesi yüklü değil, diyagram gösterilemiyor.")

    st.markdown("---")
    st.markdown("#### 🛠️ Teknoloji Yığını (Tech Stack)")
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.info("**Ingestion**")
        st.markdown("- **Kafka:** 7.5.0\n- **FastAPI:** 0.100\n- **WebSockets:** Real-time")
    with t2:
        st.info("**Processing**")
        st.markdown("- **Spark:** 3.4.1\n- **Delta Lake:** 2.4.0\n- **dbt:** 1.5.0")
    with t3:
        st.info("**Storage**")
        st.markdown("- **MinIO:** S3 Compatible\n- **PostgreSQL:** 15.0\n- **Parquet:** Columnar")
    with t4:
        st.info("**DevOps**")
        st.markdown("- **Docker:** Compose\n- **Airflow:** 2.7.1\n- **GitHub:** CI/CD")

with tab_self:
    st.markdown("#### 🛠️ Görsel Sorgu Oluşturucu (Visual Query Builder)")
    if POSTGRES_AVAILABLE:
        try:
            conn = psycopg2.connect(host="postgres", database="market_db", user="admin", password="admin")
            tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", conn)['table_name'].tolist()
            
            conf_c, viz_c = st.columns([1, 3])
            with conf_c:
                t_name = st.selectbox("Tablo Seç", tables)
                df_q = pd.read_sql(f"SELECT * FROM {t_name} LIMIT 5000", conn)
                
                c_t = st.selectbox("Grafik Tipi", ["Line", "Bar", "Scatter", "Area"])
                x_ax = st.selectbox("X Ekseni", df_q.columns)
                y_ax = st.selectbox("Y Ekseni", df_q.select_dtypes(include=np.number).columns)
                color_v = st.selectbox("Renk Ayrımı (Opsiyonel)", [None] + df_q.columns.tolist())
            
            with viz_c:
                if c_t == "Line": f_s = px.line(df_q, x=x_ax, y=y_ax, color=color_v, template="plotly_white")
                elif c_t == "Bar": f_s = px.bar(df_q, x=x_ax, y=y_ax, color=color_v, template="plotly_white")
                elif c_t == "Area": f_s = px.area(df_q, x=x_ax, y=y_ax, color=color_v, template="plotly_white")
                else: f_s = px.scatter(df_q, x=x_ax, y=y_ax, color=color_v, template="plotly_white")
                st.plotly_chart(f_s, use_container_width=True)
            conn.close()
        except Exception as e: st.error(f"SQL Bağlantı Hatası: {e}")

with tab_logs:
    st.markdown("### 🖥️ Sistem Durumu ve Loglar")
    cpu, mem, cnt = get_system_metrics()
    l1, l2, l3 = st.columns(3)
    l1.metric("CPU Kullanımı", f"%{cpu}")
    l2.metric("RAM Kullanımı", f"%{mem}")
    l3.metric("Aktif Konteyner", cnt)
    
    st.subheader("Canlı Konteyner Logları")
    logs = get_real_container_logs()
    log_html = "".join([f"<div style='color:#00FF00; font-family:monospace; font-size:12px; border-bottom:1px solid #333;'>[{l['ts']}] <b>{l['comp']}</b>: {l['msg']}</div>" for l in logs])
    st.markdown(f"<div style='background:#1E1E1E; padding:15px; border-radius:8px; height:400px; overflow-y:auto;'>{log_html}</div>", unsafe_allow_html=True)

with tab_sql:
    st.markdown("### 💾 SQL Editörü")
    q = st.text_area("SQL Sorgusu:", "SELECT * FROM crypto_prices ORDER BY processed_time DESC LIMIT 10", height=150)
    if st.button("Sorguyu Çalıştır", type="primary"):
        try:
            conn = psycopg2.connect(host="postgres", database="market_db", user="admin", password="admin")
            st.dataframe(pd.read_sql(q, conn), use_container_width=True)
            conn.close()
        except Exception as e: st.error(f"SQL Hatası: {e}")

time.sleep(refresh_rate)
st.rerun()
