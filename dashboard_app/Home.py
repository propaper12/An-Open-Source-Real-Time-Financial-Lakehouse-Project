import streamlit as st
import pandas as pd
import time
from utils import inject_custom_css, get_db_conn

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Financial Lakehouse HQ", 
    layout="wide",
    page_icon="🧠"
)

# CSS ENJEKSİYONU
inject_custom_css()

# --- HEADER (BAŞLIK ALANI) ---
c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.title("Financial Lakehouse HQ")
    st.markdown("""
    **Enterprise Data Pipeline Komuta Merkezi.** Uçtan uca veri akışını yönetin, mikroservisleri izleyin ve yapay zeka modellerini eğitin.
    """)
with c2:
    st.image("https://cdn-icons-png.flaticon.com/512/9676/9676527.png", width=80)

st.divider()

# --- BÖLÜM 1: SİSTEM MİMARİSİ (GRAPHVIZ) ---
st.subheader("📡 Canlı Sistem Mimarisi")

architecture_code = """
digraph G {
    rankdir=LR;
    bgcolor="transparent"; 
    
    node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10, margin=0.2, fontcolor="white"];
    edge [color="#555555", arrowsize=0.8, fontsize=10, fontcolor="white"];

    subgraph cluster_source {
        label = "Ingestion Layer"; style=dashed; color="#ff9900"; fontcolor="#ff9900"; bgcolor="#1E2127";
        Binance [label="Binance API", fillcolor="#FCD535", fontcolor="black"]; 
        Producer [label="Producer\n(Python)", fillcolor="#333333", color="#ff9900"];
    }
    subgraph cluster_streaming {
        label = "Streaming Layer"; style=dashed; color="#00ADB5"; fontcolor="#00ADB5"; bgcolor="#1E2127";
        Kafka [label="Apache Kafka\nCluster", fillcolor="#00ADB5", fontcolor="black"];
    }
    subgraph cluster_processing {
        label = "Processing & AI"; style=dashed; color="#ff3300"; fontcolor="#ff3300"; bgcolor="#1E2127";
        Spark [label="Spark Streaming", fillcolor="#ff5733"]; 
        ML_Trainer [label="AutoML Bot", fillcolor="#C13584"];
    }
    subgraph cluster_storage {
        label = "Lakehouse Storage"; style=dashed; color="#3366cc"; fontcolor="#3366cc"; bgcolor="#1E2127";
        MinIO [label="MinIO\n(Delta Lake)", fillcolor="#3366cc"]; 
        Postgres [label="PostgreSQL\n(Serving)", fillcolor="#2a4561"];
    }
    subgraph cluster_serving {
        label = "User Interface"; style=dashed; color="#009933"; fontcolor="#009933"; bgcolor="#1E2127";
        Streamlit [label="Dashboard app", fillcolor="#009933"]; 
        MLflow [label="MLflow Registry", fillcolor="#0099cc"];
    }

    Binance -> Producer; Producer -> Kafka; Kafka -> Spark;
    Spark -> MinIO [color="#00ADB5"]; Spark -> Postgres; 
    MinIO -> ML_Trainer; ML_Trainer -> MLflow; 
    ML_Trainer -> MinIO; Postgres -> Streamlit [color="#00ADB5", penwidth=2]; 
    Spark -> MLflow;
}
"""
try:
    st.graphviz_chart(architecture_code, use_container_width=True)
except:
    st.warning("Mimari şema yüklenemedi. Graphviz kurulu olmayabilir.")

st.divider()

# --- BÖLÜM 2: SERVİS ERİŞİM NOKTALARI ---
st.subheader("🛠️ Servis Erişim Noktaları")
st.markdown("Mikroservis yönetim panellerine güvenli erişim sağlayın.")

services = [
    {
        "icon": "🧪", "name": "MLflow Tracking", 
        "url": "http://localhost:5000", 
        "user": "-", "pass": "-", 
        "desc": "Model deneylerini ve metrikleri takip edin."
    },
    {
        "icon": "🗄️", "name": "MinIO Console", 
        "url": "http://localhost:9001", 
        "user": "admin", "pass": "admin12345", 
        "desc": "Object Storage (S3) bucket yönetimi."
    },
    {
        "icon": "📊", "name": "Metabase BI", 
        "url": "http://localhost:3005", 
        "user": "Setup", "pass": "-", 
        "desc": "Gelişmiş İş Zekası ve SQL raporlama."
    },
    {
        "icon": "📈", "name": "Grafana Monitor", 
        "url": "http://localhost:3001", 
        "user": "admin", "pass": "admin", 
        "desc": "CPU, RAM ve Docker log izleme."
    },
    {
        "icon": "⚡", "name": "FastAPI Docs", 
        "url": "http://localhost:8000/docs", 
        "user": "-", "pass": "-", 
        "desc": "Backend API Swagger dokümantasyonu."
    },
    {
        "icon": "🐳", "name": "CAdvisor", 
        "url": "http://localhost:8090/containers/", 
        "user": "-", "pass": "-", 
        "desc": "Konteyner performans metrikleri."
    }
]

# Kartları 3'lü kolon düzeninde yerleştirme
cols = st.columns(3)

for i, service in enumerate(services):
    col = cols[i % 3]
    with col:
        with st.container(border=True):
            # İkon ve Başlık
            c_icon, c_text = st.columns([1, 4])
            with c_icon:
                st.markdown(f"<h1 style='text-align: center;'>{service['icon']}</h1>", unsafe_allow_html=True)
            with c_text:
                st.markdown(f"**{service['name']}**")
                st.caption(service['desc'])
            
            # Detaylar
            with st.expander("Giriş Bilgileri"):
                if service['name'] == "Metabase BI":
                    st.code("User: admin\nPass: admin\nDB: market_db", language="yaml")
                elif service['user'] != "-":
                    st.code(f"User: {service['user']}\nPass: {service['pass']}", language="yaml")
                else:
                    st.success("Açık Erişim")

            # Buton
            st.link_button(f" {service['name']} Aç", service['url'], use_container_width=True)

st.markdown("---")
st.caption("© 2026 Real-Time Financial Lakehouse | Architect: Ömer Çakan")

# ==============================================================================
# 🔔 BİLDİRİM MERKEZİ (NOTIFICATION CENTER)
# Sol Sidebar'da çalışır, veritabanından logları çeker ve canlı gösterir.
# ==============================================================================

with st.sidebar:
    st.divider()
    st.subheader("🔔 Canlı Bildirimler")
    
    conn = get_db_conn()
    if conn:
        try:
            # Son 15 olayı getir
            query = """
                SELECT level, message, source, to_char(created_at, 'HH24:MI:SS') as saat 
                FROM system_alerts 
                ORDER BY created_at DESC LIMIT 15
            """
            df_alerts = pd.read_sql(query, conn)
            
            if not df_alerts.empty:
                for idx, row in df_alerts.iterrows():
                    
                    # Seviyeye göre Renk ve İkon
                    if row['level'] == 'ERROR':
                        icon = "🔥"
                        border_color = "#FF4B4B"
                        bg_color = "rgba(255, 75, 75, 0.1)"
                    elif row['level'] == 'WARNING':
                        icon = "⚠️"
                        border_color = "#FFAA00"
                        bg_color = "rgba(255, 170, 0, 0.1)"
                    elif row['level'] == 'SUCCESS':
                        icon = "✅"
                        border_color = "#00ADB5"
                        bg_color = "rgba(0, 173, 181, 0.1)"
                    else:
                        icon = "ℹ️"
                        border_color = "#808495"
                        bg_color = "rgba(128, 132, 149, 0.1)"

                    # HTML Kart Tasarımı
                    st.markdown(f"""
                    <div style="
                        background-color: {bg_color}; 
                        padding: 10px; 
                        border-radius: 6px; 
                        margin-bottom: 8px; 
                        border-left: 4px solid {border_color};">
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: #ccc;">
                            <span>{icon} <b>{row['source']}</b></span>
                            <span>{row['saat']}</span>
                        </div>
                        <div style="color: white; font-size: 13px; margin-top: 4px;">
                            {row['message']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Temizle Butonu
                if st.button("🗑️ Tümünü Temizle", use_container_width=True):
                    cur = conn.cursor()
                    cur.execute("DELETE FROM system_alerts;")
                    conn.commit()
                    st.rerun()
            else:
                st.success("Sistem stabil. Yeni bildirim yok.")
                
        except Exception as e:
            st.error(f"Bildirim hatası: {e}")
            
        finally:
            conn.close()
    else:
        st.warning("Veritabanı bağlantısı bekleniyor...")

    # CANLI YENİLEME (AUTO-REFRESH)
    # Bildirimlerin anlık düşmesi için sayfayı 3 saniyede bir yeniler.
    time.sleep(3) 
    st.rerun()