import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from admin_modules.minio_ops import render_minio_tab
    from admin_modules.db_ops import render_postgres_tab
    from admin_modules.metabase_ops import render_metabase_tab
except ImportError as e:
    st.error(f"Modüller yüklenemedi! Lütfen 'admin_modules' klasörünün varlığını kontrol edin. Hata: {e}")
    st.stop()

st.set_page_config(page_title="Sistem Yönetimi", layout="wide")

st.header("🔧 Enterprise Control Center")
st.markdown("Veri altyapısını ve servisleri buradan yönetebilirsiniz.")

# Sekmeler
tabs = st.tabs([" MinIO (Data Lake)", " PostgreSQL (DB)", " Metabase (BI)"])

with tabs[0]:
    render_minio_tab()

with tabs[1]:
    render_postgres_tab()

with tabs[2]:
    render_metabase_tab()