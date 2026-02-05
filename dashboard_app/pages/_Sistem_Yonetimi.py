import streamlit as st
import sys
import os
import docker
import pandas as pd
import psutil  # Sistem kaynakları için

# --- MODÜL YOLU AYARLARI ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- MODÜLLERİ YÜKLE ---
try:
    from admin_modules.minio_ops import render_minio_tab
    from admin_modules.db_ops import render_postgres_tab
    from admin_modules.metabase_ops import render_metabase_tab
except ImportError as e:
    st.error(f"⚠️ Kritik Modül Hatası: 'admin_modules' klasörü veya dosyaları eksik. Hata: {e}")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sistem Yönetimi", layout="wide", page_icon="🛠️")

st.title("🛠️ Enterprise Control Center")
st.markdown("Veri altyapısı, servis sağlığı ve kaynak tüketimi.")

st.divider()

# ==========================================
# BÖLÜM 1: SUNUCU KAYNAK İZLEME (HOST METRICS)
# ==========================================
st.subheader("🖥️ Sunucu Kaynak Durumu (Host Metrics)")

try:
    # Anlık verileri çek
    cpu_percent = psutil.cpu_percent(interval=1)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    # 3 Kolonlu Gösterge Paneli
    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric("CPU Kullanımı", f"%{cpu_percent}", delta_color="inverse")
        st.progress(cpu_percent / 100)

    with kpi2:
        mem_usage_gb = mem_info.used / (1024 ** 3)
        mem_total_gb = mem_info.total / (1024 ** 3)
        st.metric("RAM Kullanımı", f"{mem_usage_gb:.1f} / {mem_total_gb:.1f} GB", f"%{mem_info.percent}")
        st.progress(mem_info.percent / 100)

    with kpi3:
        disk_usage_gb = disk_info.used / (1024 ** 3)
        disk_total_gb = disk_info.total / (1024 ** 3)
        st.metric("Disk Alanı (Kök Dizin)", f"{disk_usage_gb:.1f} / {disk_total_gb:.1f} GB", f"%{disk_info.percent}")
        st.progress(disk_info.percent / 100)

except Exception as e:
    st.warning(f"Sistem kaynak bilgileri alınamadı: {e}")

st.divider()

# ==========================================
# BÖLÜM 2: DOCKER SERVİS SAĞLIĞI (AKILLI MOD)
# ==========================================
st.subheader("📦 Konteyner Sağlığı ve Durum Analizi")

try:
    client = docker.from_env()
    all_containers = client.containers.list(all=True) # Tüm konteynerleri bir kere çek
    
    # Aranacak anahtar kelimeler (Tam isim olmak zorunda değil)
    service_keywords = {
        "Binance Producer": "producer",
        "Apache Kafka": "kafka",
        "Zookeeper": "zookeeper",
        "Spark Streaming": "spark",
        "PostgreSQL DB": "postgres",
        "MinIO (S3)": "minio",
        "MLflow Tracking": "mlflow", # Artık içinde 'mlflow' geçen her şeyi bulur
        "AutoML Trainer": "trainer",
        "Streamlit Dashboard": "dashboard"
    }
    
    container_data = []
    
    for display_name, keyword in service_keywords.items():
        # Listeden ismi eşleşen ilk konteyneri bul (Fuzzy Search)
        found_container = next((c for c in all_containers if keyword in c.name), None)
        
        if found_container:
            status = found_container.status
            if status == "running":
                state_icon = "🟢 ÇALIŞIYOR"
            elif status == "exited":
                state_icon = "🔴 DURDU"
            else:
                state_icon = f"🟡 {status.upper()}"
                
            container_data.append({
                "Servis Adı": display_name,
                "Gerçek Konteyner ID": found_container.name, # Debug için gerçek adı görelim
                "Durum": state_icon,
                "ID": found_container.short_id
            })
        else:
            container_data.append({
                "Servis Adı": display_name, 
                "Gerçek Konteyner ID": "-",
                "Durum": "⚠️ BULUNAMADI", 
                "ID": "-"
            })

    # Tabloyu Göster
    df_containers = pd.DataFrame(container_data)
    st.dataframe(
        df_containers, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Durum": st.column_config.TextColumn("Durum"),
            "Servis Adı": st.column_config.TextColumn("Servis", width="medium"),
        }
    )

except Exception as e:
    st.error(f"Docker bağlantı hatası: {e}")

st.divider()

# ==========================================
# BÖLÜM 3: YÖNETİM SEKMELERİ
# ==========================================
tabs = st.tabs(["🪵 Canlı Log İzleyici", "💾 MinIO Yönetimi", "🐘 Veritabanı (Postgres)", "📊 Metabase (BI)"])

# --- TAB 1: LOG İZLEYİCİ ---
with tabs[0]:
    c1, c2 = st.columns([1, 4])
    
    with c1:
        # Selectbox için mevcut çalışan konteynerlerin isimlerini al
        running_names = [c.name for c in client.containers.list()] if 'client' in locals() else []
        
        if running_names:
            selected_container_name = st.selectbox("İncelenecek Servis:", running_names)
            lines = st.slider("Okunacak Satır Sayısı", 20, 1000, 100)
            
            if st.button("🔄 Logları Güncelle", use_container_width=True):
                st.rerun()
        else:
            st.warning("Hiçbir aktif konteyner bulunamadı.")
            selected_container_name = None
            
    with c2:
        if selected_container_name:
            try:
                container = client.containers.get(selected_container_name)
                logs = container.logs(tail=lines).decode("utf-8")
                st.code(logs, language="bash")
            except Exception as e:
                st.info(f"Log okunamadı: {e}")

# --- TAB 2, 3, 4: DIŞ MODÜLLER ---
with tabs[1]:
    render_minio_tab()

with tabs[2]:
    render_postgres_tab()

with tabs[3]:
    render_metabase_tab()

# ŞEMA KISMI TAMAMEN KALDIRILDI.