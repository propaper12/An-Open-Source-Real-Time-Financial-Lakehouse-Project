import streamlit as st
import sys
import os
import docker
import pandas as pd
import psutil 
import time

# --- MODÜL YOLU AYARLARI ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- HARİCİ MODÜLLERİ YÜKLE ---
try:
    from admin_modules.minio_ops import render_minio_tab
    from admin_modules.db_ops import render_postgres_tab
    from admin_modules.metabase_ops import render_metabase_tab
except ImportError as e:
    def render_minio_tab(): st.error("MinIO Modülü Eksik")
    def render_postgres_tab(): st.error("Postgres Modülü Eksik")
    def render_metabase_tab(): st.error("Metabase Modülü Eksik")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="System Control Plane", layout="wide", page_icon="🎛️")

# --- DATAROBOT / ENTERPRISE STİLİ CSS ---
st.markdown("""
<style>
    /* Ana Arka Plan - Derin Koyu Gri */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Kartlar (Containers) */
    [data-testid="stContainer"] {
        background-color: #161920;
        border: 1px solid #303339;
        border-radius: 6px;
        padding: 15px;
    }
    
    /* Metrikler */
    [data-testid="stMetricValue"] {
        color: #00ADB5 !important; /* DataRobot Turkuazı */
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
    }
    
    /* Sekmeler */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2127;
        border-radius: 4px;
        color: #FAFAFA;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ADB5 !important;
        color: #FFFFFF !important;
    }

    /* Butonlar */
    .stButton button {
        background-color: #262930;
        border: 1px solid #00ADB5;
        color: #00ADB5;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #00ADB5;
        color: white;
        box-shadow: 0 0 10px rgba(0, 173, 181, 0.5);
    }
    
    /* Kod Blokları (Loglar için) */
    code {
        color: #e6e6e6;
        background-color: #000000 !important;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ALANI ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🎛️ Enterprise Control Plane")
    st.caption("Altyapı Sağlığı • Operasyonel Bakım • Veri Yönetimi")
with c2:
    st.markdown("<div style='text-align: right; color: #00ADB5;'>v2.5.0 (Live Logs)</div>", unsafe_allow_html=True)

st.markdown("---")

# --- BÖLÜM 1: HOST METRICS (KOKPİT) ---
st.subheader("🖥️ Sunucu Kaynakları (Host Telemetry)")

try:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    k1, k2, k3 = st.columns(3)

    with k1:
        with st.container(border=True):
            st.markdown("**🔥 CPU Yükü**")
            st.metric("Core Usage", f"%{cpu_percent}", label_visibility="collapsed")
            st.progress(cpu_percent / 100)

    with k2:
        with st.container(border=True):
            mem_gb = mem_info.used / (1024 ** 3)
            total_gb = mem_info.total / (1024 ** 3)
            st.markdown("**🧠 RAM Kullanımı**")
            st.metric("Memory", f"{mem_gb:.1f} / {total_gb:.1f} GB", f"%{mem_info.percent}", label_visibility="collapsed")
            st.progress(mem_info.percent / 100)

    with k3:
        with st.container(border=True):
            disk_gb = disk_info.used / (1024 ** 3)
            st.markdown("**💾 Disk Durumu**")
            st.metric("Storage", f"{disk_gb:.1f} GB", f"%{disk_info.percent} Dolu", label_visibility="collapsed")
            st.progress(disk_info.percent / 100)

except Exception as e:
    st.error(f"Host verisi alınamadı: {e}")

st.markdown("---")

# --- BÖLÜM 2: KONTEYNER DURUMU ---
st.subheader("📦 Mikroservis Sağlığı")

try:
    client = docker.from_env()
    all_containers = client.containers.list(all=True)
    
    service_map = {
        "producer": "Binance Ingestion",
        "kafka": "Kafka Broker",
        "spark-silver": "Spark Engine (AI)",
        "postgres": "PostgreSQL DB",
        "minio": "MinIO Lakehouse",
        "mlflow_server": "MLflow Registry",
        "dashboard": "Streamlit UI",
        "api_gateway": "Universal API"
    }
    
    grid_cols = st.columns(4)
    
    for i, (key, label) in enumerate(service_map.items()):
        container = next((c for c in all_containers if key in c.name), None)
        col = grid_cols[i % 4]
        
        with col:
            with st.container(border=True):
                if container:
                    status = container.status
                    icon = "🟢" if status == "running" else "🔴" if status == "exited" else "🟡"
                    st.markdown(f"**{label}**")
                    st.markdown(f"{icon} `{status.upper()}`")
                else:
                    st.markdown(f"**{label}**")
                    st.markdown("⚪ `OFFLINE`")
    
except Exception as e:
    st.warning(f"Docker bağlantı hatası: {e}")

st.markdown("---")

# --- BÖLÜM 3: YÖNETİM SEKMELERİ ---
tabs = st.tabs([
    "🛠️ Bakım & Kalite (OPS)", 
    "📜 Canlı Loglar", 
    "🗄️ Lakehouse (MinIO)", 
    "🐘 Veritabanı (SQL)", 
    "📊 BI Raporlama"
])

# --- SEKME 1: OPERASYONEL BAKIM (GÜNCELLENEN KISIM) ---
with tabs[0]:
    c_ops1, c_ops2 = st.columns(2)
    
    # --- SOL: BAKIM (MAINTENANCE) ---
    with c_ops1:
        with st.container(border=True):
            st.subheader("🧹 Delta Lake Bakım Motoru")
            st.info("Küçük dosyaları birleştirir (Optimize) ve 1 saatten eski çöpleri siler (Vacuum).")
            
            # Butona basınca status container açılacak ve loglar içine akacak
            if st.button("🚀 SİSTEM BAKIMINI BAŞLAT", type="primary", use_container_width=True):
                # 'expanded=True' ile logları açık tutuyoruz
                with st.status("Spark Engine'e Bağlanılıyor...", expanded=True) as status:
                    try:
                        st.write("🔌 Docker soketine erişiliyor...")
                        container = client.containers.get("spark-silver")
                        
                        st.write("⚙️ `maintenance_job.py` çalıştırılıyor...")
                        # exec_run komutu script bitene kadar bekler (blocking)
                        exec_result = container.exec_run("python maintenance_job.py")
                        output = exec_result.output.decode("utf-8")
                        
                        st.write("📄 Log çıktısı alınıyor...")
                        
                        # Logları Ekrana Bas (Karanlık Modda)
                        st.code(output, language="bash")
                        
                        if exec_result.exit_code == 0:
                            status.update(label="✅ Bakım Başarıyla Tamamlandı!", state="complete", expanded=True)
                        else:
                            status.update(label="❌ Hata Oluştu", state="error", expanded=True)
                            
                    except Exception as e:
                        status.update(label="Bağlantı Hatası", state="error")
                        st.error(str(e))

    # --- SAĞ: KALİTE (QUALITY) ---
    with c_ops2:
        with st.container(border=True):
            st.subheader("🛡️ Veri Kalite Kapısı")
            st.info("Silver katmanını tarar. Negatif fiyat, null değer ve hatalı zaman damgalarını raporlar.")
            
            if st.button("🔍 KALİTE KONTROLÜNÜ ÇALIŞTIR", use_container_width=True):
                # 'expanded=True' logları anında gösterir
                with st.status("Veri Analizi Başlatılıyor...", expanded=True) as status:
                    try:
                        st.write("🧪 Spark analiz motoru hazırlanıyor...")
                        container = client.containers.get("spark-silver")
                        
                        st.write("🔎 `quality_gate.py` ile veri taranıyor...")
                        exec_result = container.exec_run("python quality_gate.py")
                        output = exec_result.output.decode("utf-8")
                        
                        st.write("📊 Rapor oluşturuluyor...")
                        
                        # Logları Renkli Göster (YAML formatı okumayı kolaylaştırır)
                        st.code(output, language="yaml")
                        
                        if "BAŞARILI" in output or "PASSED" in output:
                            status.update(label="✅ Kalite: MÜKEMMEL", state="complete", expanded=True)
                        elif "FAILED" in output:
                            status.update(label="⚠️ Kalite: SORUNLU", state="error", expanded=True)
                        else:
                            status.update(label="İşlem Bitti", state="complete", expanded=True)
                        
                    except Exception as e:
                        status.update(label="Sistem Hatası", state="error")
                        st.error(str(e))

# --- SEKME 2: LOG İZLEYİCİ ---
with tabs[1]:
    col_sel, col_log = st.columns([1, 4])
    with col_sel:
        st.markdown("**Hedef Servis**")
        running_names = [c.name for c in client.containers.list()] if client else []
        selected_container = st.selectbox("Seçiniz:", running_names, label_visibility="collapsed")
        lines = st.slider("Satır Sayısı", 50, 500, 100)
        if st.button("🔄 Yenile", use_container_width=True):
            st.rerun()
            
    with col_log:
        if selected_container:
            try:
                container = client.containers.get(selected_container)
                logs = container.logs(tail=lines).decode("utf-8")
                st.code(logs, language="bash")
            except Exception as e:
                st.error(f"Log okunamadı: {e}")

with tabs[2]: render_minio_tab()
with tabs[3]: render_postgres_tab()
with tabs[4]: render_metabase_tab()

st.markdown("---")
st.caption("© 2026 Lakehouse Operations | Architect: Ömer Çakan | Powered by Streamlit & Docker")