import streamlit as st
import socket

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Financial Lakehouse HQ", 
    layout="wide",
    page_icon="🏠"
)

# --- BAŞLIK ---
st.title("🏠 Financial Lakehouse HQ")
st.markdown("""
**Komuta Merkezine Hoşgeldiniz.** Bu platform, **End-to-End (Uçtan Uca)** veri mühendisliği pipeline'larını yönetir, izler ve raporlar.
""")

st.divider()

# ==========================================
# BÖLÜM 1: SİSTEM MİMARİSİ (VİTRİN)
# ==========================================
st.subheader("🗺️ Proje Mimarisi ve Veri Akışı")
st.markdown("Verinin **Binance** kaynağından çıkıp **Son Kullanıcı** ekranına gelene kadar izlediği yol.")

architecture_code = """
digraph G {
    rankdir=LR;
    node [shape=box, style="filled,rounded", fontname="Sans-Serif", margin=0.2];
    edge [color="#666666", arrowsize=0.8, fontsize=10];

    subgraph cluster_source {
        label = "Ingestion"; style=dashed; color="#ff9900"; bgcolor="#fffdf5";
        Binance [label="Binance API", fillcolor="#FCD535"]; Producer [label="Producer", fillcolor="#ffcc99"];
    }
    subgraph cluster_streaming {
        label = "Streaming"; style=dashed; color="#000000"; bgcolor="#f5f5f5";
        Kafka [label="Kafka", fillcolor="#333333", fontcolor="white"];
    }
    subgraph cluster_processing {
        label = "Processing & ML"; style=dashed; color="#ff3300"; bgcolor="#fff5f2";
        Spark [label="Spark Streaming", fillcolor="#ff5733", fontcolor="white"]; ML_Trainer [label="AutoML Bot", fillcolor="#ffcc00"];
    }
    subgraph cluster_storage {
        label = "Storage"; style=dashed; color="#3366cc"; bgcolor="#f2f7ff";
        MinIO [label="MinIO (Delta)", fillcolor="#ff9999"]; Postgres [label="PostgreSQL", fillcolor="#3366cc", fontcolor="white"];
    }
    subgraph cluster_serving {
        label = "UI & Monitoring"; style=dashed; color="#009933"; bgcolor="#f2fff5";
        Streamlit [label="Dashboard", fillcolor="#ff4b4b", fontcolor="white"]; MLflow [label="MLflow", fillcolor="#0099cc", fontcolor="white"];
    }

    Binance -> Producer; Producer -> Kafka; Kafka -> Spark;
    Spark -> MinIO; Spark -> Postgres; MinIO -> ML_Trainer;
    ML_Trainer -> MLflow; ML_Trainer -> MinIO; Postgres -> Streamlit; Spark -> MLflow;
}
"""
try:
    st.graphviz_chart(architecture_code, use_container_width=True)
except:
    st.warning("Mimari şema yüklenemedi.")

st.divider()

# ==========================================
# BÖLÜM 2: SERVİS ERİŞİM NOKTALARI
# ==========================================
st.subheader("🚀 Servis Erişim Noktaları & Araçlar")
st.markdown("Sistemi oluşturan mikroservislerin yönetim panellerine buradan erişebilirsiniz.")

# Servis Listesi (Airflow hariç hepsi)
services = [
    {
        "icon": "🧠", "name": "MLflow Tracking", 
        "url": "http://localhost:5000", 
        "user": "-", "pass": "-", 
        "desc": "Model deneylerini, metrikleri ve parametreleri takip edin."
    },
    {
        "icon": "🗄️", "name": "MinIO Console", 
        "url": "http://localhost:9001", 
        "user": "admin", "pass": "admin12345", 
        "desc": "Object Storage (S3) dosya gezgini ve bucket yönetimi."
    },
    {
        "icon": "📈", "name": "Metabase BI", 
        "url": "http://localhost:3005", 
        "user": "Setup", "pass": "-", 
        "desc": "SQL tabanlı iş zekası raporlama ve dashboard aracı."
    },
    {
        "icon": "📊", "name": "Grafana Monitor", 
        "url": "http://localhost:3001", 
        "user": "admin", "pass": "admin", 
        "desc": "Sistem kaynakları (CPU/RAM) ve log görselleştirme."
    },
    {
        "icon": "🔌", "name": "FastAPI Docs", 
        "url": "http://localhost:8000/docs", 
        "user": "-", "pass": "-", 
        "desc": "Backend API uç noktaları (Swagger UI)."
    },
    {
        "icon": "🐋", "name": "CAdvisor", 
        "url": "http://localhost:8090/containers/", 
        "user": "-", "pass": "-", 
        "desc": "Docker konteynerlerinin anlık performans metrikleri."
    }
]

# Grid Düzeni (2 Kolonlu)
c1, c2 = st.columns(2)
grid_cols = [c1, c2]

for i, service in enumerate(services):
    col = grid_cols[i % 2] # Sırayla sol-sağ dağıt
    
    with col:
        with st.container(border=True):
            # Üst Kısım: İkon ve Başlık
            sub_c1, sub_c2 = st.columns([1, 4])
            with sub_c1:
                st.markdown(f"# {service['icon']}")
            with sub_c2:
                st.subheader(service['name'])
                st.caption(service['desc'])
            
            st.divider()
            
            # Orta Kısım: Şifreler ve Detaylar
            if service['name'] == "Metabase BI":
                with st.expander("📝 Kurulum Bilgileri (Tıkla)"):
                    st.info("""
                    **Database Type:** PostgreSQL
                    **Host:** postgres
                    **DB Name:** market_db
                    **User:** admin
                    **Password:** admin
                    """)
                    st.warning("İlk girişte 'Setup' ekranı gelecektir.")
            
            elif service['user'] != "-":
                k1, k2 = st.columns(2)
                with k1:
                    st.text("Kullanıcı Adı:")
                    st.code(service['user'], language="text")
                with k2:
                    st.text("Şifre:")
                    st.code(service['pass'], language="text")
            else:
                st.success("🔓 Kimlik doğrulama gerekmez (Açık Erişim)")

            # Alt Kısım: Buton
            st.markdown("")
            st.link_button(f"↗️ {service['name']} Paneline Git", service['url'], use_container_width=True)

st.markdown("---")
st.caption("© 2026 Real-Time Financial Lakehouse | v4.0 Stable")