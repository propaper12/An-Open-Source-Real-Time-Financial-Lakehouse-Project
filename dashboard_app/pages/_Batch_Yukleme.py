import streamlit as st
import pandas as pd
import sys
import os
import subprocess
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_s3_fs, BUCKET_NAME

st.set_page_config(page_title="Batch Upload", layout="wide")
st.header(" Batch Data Upload (Geçmiş Veri Yükleme)")

col1, col2 = st.columns([1, 1])

with col1:
    st.info("Bu modül, elinizdeki CSV dosyalarını (Örn: Geçen yılın satış verileri) sisteme dahil eder.")
    
    with st.expander("CSV Formatı Nasıl Olmalı?"):
        st.markdown("""
        Dosyanız şu sütunları içermelidir:
        * `symbol` (Örn: GARAN.IS)
        * `price` (Örn: 54.20)
        * `quantity` (Örn: 100)
        * `timestamp` (Opsiyonel)
        """)
        
    uploaded_file = st.file_uploader("Veri Seti (CSV)", type=['csv'])

if uploaded_file:
    try:
        df_preview = pd.read_csv(uploaded_file)
        with col2:
            st.subheader(" Dosya Önizleme")
            st.dataframe(df_preview.head(5), use_container_width=True)
    except:
        st.error("Dosya okunamadı. CSV formatını kontrol edin.")

    if st.button(" 1. Adım: Data Lake'e Gönder", type="primary"):
        try:
            s3 = get_s3_fs()
            file_name = uploaded_file.name.replace(" ", "_") 
            target_path = f"{BUCKET_NAME}/raw_batch_uploads/{file_name}"
            
            with s3.open(target_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            st.success(f" Dosya MinIO'ya yüklendi: {target_path}")
            st.session_state['last_uploaded_file'] = file_name
            
        except Exception as e:
            st.error(f"Yükleme Hatası: {e}")

    if 'last_uploaded_file' in st.session_state:
        st.markdown("---")
        st.write(f"Sırada: **{st.session_state['last_uploaded_file']}** dosyasını işlemek var.")
        
        if st.button(" 2. Adım: Spark Batch İşlemini Başlat"):
            with st.status("Spark Job Çalışıyor...", expanded=True) as status:
                st.write(" Docker konteynerine bağlanılıyor...")
                time.sleep(1)
                
                file_name = st.session_state['last_uploaded_file']
                cmd = ["docker", "exec", "spark-silver", "python", "/app/batch_processor.py", file_name]
                
                st.write(" Veriler işleniyor ve Delta Lake'e yazılıyor...")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    st.write(" İşlem tamamlandı.")
                    status.update(label="İşlem Başarılı!", state="complete", expanded=False)
                    st.success("Veriler başarıyla Gold katmanına eklendi! 'Canlı Piyasa' veya 'Metabase' üzerinden görebilirsiniz.")
                    # Logları göster (Opsiyonel)
                    with st.expander("Sistem Logları"):
                        st.code(result.stdout)
                else:
                    status.update(label="Hata Oluştu", state="error")
                    st.error("Spark işlemi başarısız oldu.")
                    st.error(result.stderr)