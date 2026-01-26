import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import sys
import os
import docker
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_s3_fs, BUCKET_NAME

st.set_page_config(page_title="Canlı Piyasa", layout="wide")

with st.sidebar:
    st.header("🎛️ Kontrol Merkezi")
    st.info("Sistem konteynerlerini buradan yönetebilirsiniz.")
    st.markdown("---")
    
    try:
        client = docker.from_env()
        try:
            container = client.containers.get('binance_producer')
            status = container.status
            
            st.write(f"**Veri Akışı Durumu:**")
            
            if status == 'running':
                st.success("🟢 AKTİF (Veri Akıyor)")
                if st.button("⛔ AKIŞI DURDUR", type="primary", use_container_width=True):
                    with st.spinner("Bot durduruluyor..."):
                        container.stop()
                    st.rerun()
            else:
                st.error("🔴 DURDU (Kapalı)")
                if st.button("▶️ AKIŞI BAŞLAT", type="secondary", use_container_width=True):
                    with st.spinner("Bot başlatılıyor..."):
                        container.start()
                    st.rerun()
                    
        except docker.errors.NotFound:
            st.warning("⚠️ Producer konteyneri bulunamadı.")
            
    except Exception as e:
        st.error("Docker servisine erişilemedi.")

    st.markdown("---")
    st.caption("Auto-refresh: 2s")

st.header("📈 Enterprise Real-Time Monitor")

try:
    s3 = get_s3_fs()
    
    files = s3.glob(f"s3://{BUCKET_NAME}/silver_layer_delta/**/*.parquet")
    
    if not files:
        st.warning("📡 Veri akışı bekleniyor... (MinIO'da henüz parquet dosyası oluşmadı)")
        time.sleep(3)
        st.rerun()
    else:
       
        recent_files = sorted(files)[-20:] 
        
        dfs = []
        for f in recent_files:
            try:
                temp_df = pd.read_parquet(s3.open(f))
                
                if 'symbol' not in temp_df.columns:
                    parts = f.split("/")
                    for p in parts:
                        if p.startswith("symbol="):
                            extracted_sym = p.split("=")[1]
                            temp_df['symbol'] = extracted_sym
                            break
                
                if 'symbol' in temp_df.columns:
                    dfs.append(temp_df)
                    
            except Exception as read_err:
                print(f"Dosya okuma hatası ({f}): {read_err}")
                continue

        if not dfs:
            st.warning("Veri dosyaları var ama okunabilir formatta değil. Bekleniyor...")
            time.sleep(2)
            st.rerun()
            
        df = pd.concat(dfs)
        
        available_symbols = df['symbol'].unique()
        
        if len(available_symbols) > 0:
            selected_sym = st.selectbox("İzlenecek Kaynak (Borsa / IoT)", available_symbols)
            
            df_sym = df[df['symbol'] == selected_sym].sort_values('processed_time')
            
            df_chart = df_sym.tail(100)
            
            if not df_chart.empty:
                last = df_chart.iloc[-1]
                last_time_str = str(last['processed_time'])
                
                st.markdown(f"###  Son Güncelleme: `{last_time_str}`")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Anlık Değer / Fiyat", f"{last['average_price']:,.2f} $")
                
                pred_price = last.get('predicted_price', last['average_price'])
                diff = pred_price - last['average_price']
                
                c2.metric("AI Tahmin (Gelecek)", f"{pred_price:,.2f} $", f"{diff:+.2f}")
                c3.metric("Volatilite Risk Skoru", f"{last['volatility']:.4f}")

                st.divider()

                col_graph, col_table = st.columns([2, 1])
                
                with col_graph:
                    st.subheader("📊 Canlı Analiz Grafiği")
                    fig = go.Figure()
                    
                    # Gerçek Değer
                    fig.add_trace(go.Scatter(
                        x=df_chart['processed_time'], 
                        y=df_chart['average_price'], 
                        name='Gerçek Değer',
                        line=dict(color='#00CC96', width=3)
                    ))
                    
                    if 'predicted_price' in df_chart.columns:
                        fig.add_trace(go.Scatter(
                            x=df_chart['processed_time'], 
                            y=df_chart['predicted_price'], 
                            name='AI Tahmin', 
                            line=dict(dash='dot', color='#AB63FA', width=2)
                        ))
                    
                    fig.update_layout(
                        template="plotly_dark", 
                        height=450, 
                        margin=dict(l=20, r=20, t=30, b=20),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_table:
                    st.subheader("Son Veriler")
                    df_table = df_chart.tail(15).sort_values(by='processed_time', ascending=False)
                    
                    cols_to_show = ['processed_time', 'average_price']
                    if 'predicted_price' in df_table.columns:
                        cols_to_show.append('predicted_price')
                        
                    display_table = df_table[cols_to_show].copy()
                    
                    rename_map = {
                        'processed_time': 'Zaman', 
                        'average_price': 'Fiyat ($)',
                        'predicted_price': 'AI Tahmin ($)'
                    }
                    display_table = display_table.rename(columns=rename_map)
                    
                    st.dataframe(display_table, use_container_width=True, hide_index=True, height=450)

                time.sleep(2)
                st.rerun()
            else:
                st.info(f"{selected_sym} için veri yükleniyor...")
        else:
            st.warning("Veri formatı uyuşmazlığı. Symbol bilgisi okunamadı.")
            time.sleep(2)
            st.rerun()

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
    import traceback
    st.code(traceback.format_exc())
    time.sleep(5)
    st.rerun()