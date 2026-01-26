import streamlit as st
import pandas as pd
from minio import Minio
from minio.error import S3Error
import os
from dotenv import load_dotenv

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")

def render_minio_tab():
    st.subheader(" Data Lake Explorer (MinIO)")

    
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Bucket İşlemleri")
            new_bucket = st.text_input("Yeni Bucket Adı", placeholder="örn: test-verisi")
            
            if st.button("Bucket Oluştur"):
                if new_bucket:
                    try:
                        if not client.bucket_exists(new_bucket):
                            client.make_bucket(new_bucket)
                            st.success(f" '{new_bucket}' oluşturuldu!")
                            st.rerun()
                        else:
                            st.warning("Bu isimde bucket zaten var.")
                    except S3Error as e:
                        st.error(f"MinIO Hatası: {e}")

        with col2:
            st.markdown("###  İçerik Yönetimi")
            try:
                buckets = client.list_buckets()
                bucket_names = [b.name for b in buckets]
                
                if bucket_names:
                    selected_bucket = st.selectbox("Bucket Seçin", bucket_names)
                    
                    with st.expander(f" '{selected_bucket}' Sil (ZORLA)"):
                        st.warning(" DİKKAT: Bu işlem bucket içindeki TÜM DOSYALARI siler ve geri alınamaz!")
                        
                        if st.button("Evet, Her Şeyi Sil ve Bucket'ı Uçur", type="primary"):
                            try:
                                objects = client.list_objects(selected_bucket, recursive=True)
                                
                                deleted_count = 0
                                for obj in objects:
                                    client.remove_object(selected_bucket, obj.object_name)
                                    deleted_count += 1
                                
                                client.remove_bucket(selected_bucket)
                                
                                st.success(f" Temizlik tamamlandı! {deleted_count} dosya ve Bucket silindi.")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Silme Hatası: {e}")

                    st.divider()

                    objects = client.list_objects(selected_bucket, recursive=True)
                    obj_list = list(objects)
                    
                    if obj_list:
                        file_data = [{"Dosya": o.object_name, "Boyut (KB)": round(o.size/1024, 2), "Tarih": o.last_modified} for o in obj_list]
                        st.dataframe(pd.DataFrame(file_data), use_container_width=True)
                        
                        file_to_del = st.selectbox("Silinecek Dosya", [o.object_name for o in obj_list])
                        if st.button(" Dosyayı Sil"):
                            client.remove_object(selected_bucket, file_to_del)
                            st.success(f"Silindi: {file_to_del}")
                            st.rerun()
                    else:
                        st.info("Bu bucket şu an boş.")
                else:
                    st.warning("Henüz hiç bucket yok.")

            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}")

    except Exception as e:
        st.error(f"Genel Hata: {e}")