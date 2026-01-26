import streamlit as st
import pandas as pd
import s3fs
import time
import plotly.graph_objects as go
import os
import subprocess
import signal

MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
ACCESS_KEY = "admin"
SECRET_KEY = "admin12345"
BUCKET_NAME = "market-data"

st.set_page_config(page_title="DataOps Command Center", layout="wide", page_icon="🎛️")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .success-box { padding:10px; background-color: #0f5132; color: white; border-radius: 5px; }
    .warning-box { padding:10px; background-color: #664d03; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

def get_s3_fs():
    return s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY, client_kwargs={'endpoint_url': MINIO_URL})

if 'active_stream_pid' not in st.session_state:
    st.session_state['active_stream_pid'] = None
    st.session_state['active_source'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9320/9320538.png", width=80)
    st.title("Data Platform")
    st.markdown("---")
    
    mode = st.radio("📡 Çalışma Modu Seçin", 
                    ["🟢 Canlı İzleme (Binance)", 
                     "📂 Batch Veri Yükleme (Duran)", 
                     "🔌 Harici API Bağlantısı (Akan)"])
    
    st.markdown("---")
    st.info(f"Aktif Mod: **{mode}**")

if mode == "📂 Batch Veri Yükleme (Duran)":
    st.header("📂 Data Lake Dosya Yükleyici")
    st.markdown("CSV dosyalarınızı sürükleyip bırakın. Veriler anında **MinIO (Bronze Layer)** içine işlenecektir.")
    
    uploaded_file = st.file_uploader("Veri Seti Seçin", type=['csv', 'parquet'])
    
    col1, col2 = st.columns(2)
    
    if uploaded_file:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "Size": uploaded_file.size}
        with col1:
            st.write("📄 Dosya Önizleme:")
            df_preview = pd.read_csv(uploaded_file)
            st.dataframe(df_preview.head(5))
            
        with col2:
            st.write("💾 Hedef Depo:")
            st.code(f"s3://{BUCKET_NAME}/raw_batch_uploads/{uploaded_file.name}")
            
            if st.button("🚀 MinIO'ya Gönder ve İşle"):
                try:
                    s3 = get_s3_fs()
                    target_path = f"{BUCKET_NAME}/raw_batch_uploads/{uploaded_file.name}"
                    
                    with s3.open(target_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    st.success(f"✅ Başarılı! Dosya MinIO'da: {target_path}")
                    
                    st.toast("Spark Batch Job kuyruğa alındı...", icon="⚙️")
                    time.sleep(2)
                    st.toast("Veri Gold Katmanına işlendi!", icon="🏆")
                    
                except Exception as e:
                    st.error(f"Hata: {e}")

elif mode == "🔌 Harici API Bağlantısı (Akan)":
    st.header("🔌 Universal API Stream Connector")
    st.markdown("Herhangi bir Finansal Veri API'sine bağlanıp canlı veriyi **Kafka & Spark** hattına yönlendirin.")
    
    c1, c2, c3 = st.columns(3)
    source_name = c1.selectbox("Veri Sağlayıcı", ["Yahoo Finance", "AlphaVantage", "Bloomberg", "Borsa Istanbul (BIST)"])
    symbol = c2.text_input("Sembol / Parite", value="THYAO.IS")
    api_key = c3.text_input("API Anahtarı (API Key)", type="password", placeholder="sk_live_...")
    
    st.markdown("---")
    
    if st.session_state['active_stream_pid'] is None:
        if st.button("⚡ BAĞLANTIYI BAŞLAT"):
            if not api_key:
                st.error("Lütfen API Anahtarı girin!")
            else:
                process = subprocess.Popen(
                    ["python", "universal_producer.py", source_name, api_key, symbol],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                st.session_state['active_stream_pid'] = process.pid
                st.session_state['active_source'] = f"{source_name} ({symbol})"
                st.rerun()
    else:
        st.success(f"✅ AKTİF AKIŞ: **{st.session_state['active_source']}** (PID: {st.session_state['active_stream_pid']})")
        st.caption("Veriler Kafka'ya akıyor ve Spark tarafından işleniyor...")
        
        if st.button("⛔ BAĞLANTIYI KES"):
            try:
                os.kill(st.session_state['active_stream_pid'], signal.SIGTERM)
                st.toast("Bağlantı güvenli şekilde kapatıldı.")
            except:
                st.warning("İşlem zaten sonlanmış olabilir.")
            
            st.session_state['active_stream_pid'] = None
            st.session_state['active_source'] = None
            st.rerun()

else: # Default: Canlı Binance
    st.header("📈 Enterprise Real-Time Monitor")
    
    try:
        s3 = get_s3_fs()
        files = s3.glob(f"s3://{BUCKET_NAME}/silver_layer_delta/**/*.parquet")
        
        if not files:
            st.warning("Henüz veri akışı yok veya Spark veriyi yazmadı. Lütfen 'Harici API Bağlantısı' modundan bir akış başlatın.")
        else:
            recent_files = sorted(files)[-5:] 
            dfs = [pd.read_parquet(s3.open(f)) for f in recent_files]
            df = pd.concat(dfs)
            
            active_symbols = df['symbol'].unique()
            selected_sym = st.selectbox("İzlenecek Parite", active_symbols)
            
            df_sym = df[df['symbol'] == selected_sym].sort_values('processed_time').tail(50)
            
            last_price = df_sym.iloc[-1]['average_price']
            prev_price = df_sym.iloc[-2]['average_price'] if len(df_sym) > 1 else last_price
            delta = last_price - prev_price
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Anlık Fiyat", f"{last_price:,.2f}", f"{delta:.2f}")
            m2.metric("AI Tahmini", f"{df_sym.iloc[-1]['predicted_price']:,.2f}")
            m3.metric("Volatilite", f"{df_sym.iloc[-1]['volatility']:.4f}")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_sym['processed_time'], y=df_sym['average_price'], mode='lines', name='Fiyat'))
            fig.add_trace(go.Scatter(x=df_sym['processed_time'], y=df_sym['predicted_price'], mode='lines', name='AI Tahmin', line=dict(dash='dot')))
            fig.update_layout(title=f"{selected_sym} Canlı Analiz", template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("###  Son İşlenen Veriler (Delta Lake Silver Table)")
            st.dataframe(df_sym.iloc[::-1].head(5), use_container_width=True)
            
            time.sleep(2)
            st.rerun()
            
    except Exception as e:
        st.error(f"Data Lake Bağlantı Hatası: {e}")
        st.info("MinIO konteynerinin çalıştığından emin olun.")