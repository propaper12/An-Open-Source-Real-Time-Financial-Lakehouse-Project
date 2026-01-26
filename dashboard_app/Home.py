import streamlit as st
import psutil
import socket

st.set_page_config(
    page_title="Financial Lakehouse HQ", 
    layout="wide", 
)

st.title(" Enterprise Data Platform - Komuta Merkezi")
st.markdown("Bu panel, **Real-Time Financial Lakehouse** altyapısındaki tüm servislerin durumunu ve erişim bilgilerini tek ekranda toplar.")
st.markdown("---")

col_sys1, col_sys2, col_sys3, col_sys4 = st.columns(4)

with col_sys1:
    cpu = psutil.cpu_percent()
    st.metric("Sunucu CPU", f"%{cpu}", delta_color="inverse")

with col_sys2:
    ram = psutil.virtual_memory().percent
    st.metric("RAM Kullanımı", f"%{ram}", delta_color="inverse")

with col_sys3:
    try:
        ip = socket.gethostbyname(socket.gethostname())
        st.metric("Container IP", ip)
    except:
        st.metric("Network", "Bridge")

with col_sys4:
    st.metric("Sistem Durumu", "Aktif 🟢")

st.markdown("---")

st.subheader("🔗 Servis Bağlantıları & Erişim Bilgileri")

services = [
    {
        "icon": "🌪️", "name": "Airflow", 
        "url": "http://localhost:8081", 
        "user": "admin", "pass": "admin", 
        "desc": "Pipeline Orkestrasyonu & DAG Yönetimi"
    },
    {
        "icon": "🗄️", "name": "MinIO Console", 
        "url": "http://localhost:9001", 
        "user": "admin", "pass": "admin12345", 
        "desc": "Data Lake (S3) Dosya Gezgini"
    },
    {
        "icon": "📈", "name": "Metabase BI", 
        "url": "http://localhost:3005", 
        "user": "Setup", "pass": "-", 
        "desc": "İş Zekası ve SQL Raporlama (Kurulum Gerekli)"
    },
    {
        "icon": "🧠", "name": "MLflow Tracking", 
        "url": "http://localhost:5000", 
        "user": "-", "pass": "-", 
        "desc": "Model Metrikleri ve Versiyonlama"
    },
    {
        "icon": "📊", "name": "Grafana", 
        "url": "http://localhost:3001", 
        "user": "admin", "pass": "admin", 
        "desc": "Sistem Kaynakları ve Log İzleme"
    },
    {
        "icon": "🔌", "name": "API Docs", 
        "url": "http://localhost:8000/docs", 
        "user": "-", "pass": "-", 
        "desc": "Veri Giriş Noktası Dokümantasyonu"
    },
    {
        "icon": "🐋", "name": "CAdvisor", 
        "url": "http://localhost:8090/containers/", 
        "user": "-", "pass": "-", 
        "desc": "Docker Konteyner İstatistikleri"
    }
]

row1 = st.columns(2)
row2 = st.columns(2)
row3 = st.columns(2)
row4 = st.columns(2)

grid = [col for row in [row1, row2, row3, row4] for col in row]

for i, service in enumerate(services):
    with grid[i]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {service['icon']} {service['name']}")
                st.caption(service['desc'])
            with c2:
                st.link_button("↗️ Git", service['url'], use_container_width=True)
            
            if service['name'] == "Metabase BI":
                st.warning(" İlk giriş için aşağıdaki bilgileri kullanın:")
                
                with st.expander("📝 Metabase Kurulum Adımları (Tıkla)"):
                    st.markdown("""
                    **1. Adım: Hoşgeldiniz**
                    * **Ad/Soyad/Email:** Kendi bilgilerinizi girin.
                    * **Şirket/Ekip Adı:** `Financial LakeHouse`
                    * **Şifre:** Kendi belirlediğiniz bir şifre.
                    
                    **2. Adım: Kullanım Amacı**
                    * `İkisinden de biraz` seçeneğini işaretleyin.
                    
                    **3. Adım: Verilerinizi Ekleyin (PostgreSQL Seçin)**
                    """)
                    
                    c_db1, c_db2 = st.columns(2)
                    c_db1.text_input("Display Name", "Market Data", disabled=True)
                    c_db1.text_input("Host", "postgres", disabled=True, help="Docker içindeki servis adı")
                    c_db1.text_input("Database name", "market_db", disabled=True)
                    
                    c_db2.text_input("Port", "5432", disabled=True)
                    c_db2.text_input("Username", "admin", disabled=True)
                    c_db2.text_input("Password", "admin", disabled=True)
                    
                    st.success("Bu bilgileri girdikten sonra 'Next' diyerek kurulumu tamamlayın.")

            elif service['user'] != "-":
                st.markdown("**🔑 Giriş Bilgileri:**")
                c_user, c_pass = st.columns(2)
                c_user.code(service['user'], language="text")
                c_pass.code(service['pass'], language="text")
            else:
                st.info("🔓 Kimlik doğrulama gerekmez.")

st.markdown("---")
st.caption("© 2026 Real-Time Financial Lakehouse Project | v2.4.0 Production Ready")