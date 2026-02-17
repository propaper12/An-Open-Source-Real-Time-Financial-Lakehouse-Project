import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os
import docker
from sqlalchemy import create_engine

st.set_page_config(page_title="Canlı Piyasa", layout="wide", page_icon="📈")

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# VERİTABANI BAĞLANTISI 
DB_URL = "postgresql://admin:admin@postgres:5432/market_db"

def calculate_technical_indicators(df):
    """
    Teknik İndikatörleri Hesapla: Bollinger, RSI ve MACD
    """
    # 1. Bollinger
    df['SMA_20'] = df['average_price'].rolling(window=20).mean()
    df['Std_Dev'] = df['average_price'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + (df['Std_Dev'] * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (df['Std_Dev'] * 2)
    
    # 2. RSI
    delta = df['average_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. MACD
    df['EMA12'] = df['average_price'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['average_price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df.fillna(0)

def get_data_from_db():
    try:
        engine = create_engine(DB_URL)
        query = "SELECT * FROM market_data ORDER BY processed_time DESC LIMIT 300"
        df = pd.read_sql(query, engine)
        df = df.sort_values(by='processed_time', ascending=True)
        df = calculate_technical_indicators(df)
        return df
    except Exception as e:
        st.error(f"DB Hatası: {e}")
        return pd.DataFrame()

#SIDEBAR 
with st.sidebar:
    st.header(" Kontrol Paneli")
    
    try:
        client = docker.from_env()
        container = client.containers.get('binance_producer')
        if container.status == 'running':
            st.success(" Veri Akışı: AKTİF")
            if st.button(" Durdur"): container.stop(); st.rerun()
        else:
            st.error(" Veri Akışı: DURDU")
            if st.button(" Başlat"): container.start(); st.rerun()
    except:
        st.warning("Docker bağlantısı yok.")

    st.markdown("---")
    st.subheader("Görünüm Ayarları")
    show_main = st.checkbox("Ana Fiyat Grafiği", value=True)
    show_risk = st.checkbox("Risk Analizi (Bollinger)", value=True)
    show_momentum = st.checkbox("Momentum (RSI/MACD)", value=True)

#ANA EKRAN
st.title(" Pro-Trader Cockpit")
st.caption("AI Tahminleri ve Çoklu Teknik Analiz Göstergeleri")

df = get_data_from_db()

if df.empty:
    st.warning("Veri bekleniyor...")
    time.sleep(2)
    st.rerun()
else:
    available_symbols = df['symbol'].unique()
    if len(available_symbols) > 0:
        selected_sym = st.selectbox("Varlık Seçimi", available_symbols, label_visibility="collapsed")
        df_chart = df[df['symbol'] == selected_sym]
        
        if not df_chart.empty:
            last = df_chart.iloc[-1]
            
        
            last_time_str = pd.to_datetime(last['processed_time']).strftime('%Y-%m-%d %H:%M:%S')            
            st.markdown(f"###  Son Güncelleme: `{last_time_str}` (UTC)")
            
            st.divider()

            # 1. KPI
            curr = last['average_price']
            pred = last['predicted_price']
            diff = pred - curr
            rsi = last['RSI']
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(" Fiyat", f"{curr:,.2f} $")
            k2.metric(" AI Hedef", f"{pred:,.2f} $", f"{diff:+.2f} $", delta_color="normal" if diff > 0 else "inverse")
            
            signal = "AL " if diff > 0 else "SAT "
            k3.metric("Sinyal", signal, f"Güven: %99.9")
            
            rsi_state = "Aşırı Alım" if rsi > 70 else "Aşırı Satım" if rsi < 30 else "Normal"
            k4.metric("RSI Durumu", f"{rsi:.1f}", rsi_state, delta_color="off")

            st.divider()
            
            # ANA GRAFİK
            if show_main:
                st.subheader(" Fiyat ve AI Tahmini")
                fig_main = go.Figure()
                fig_main.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['average_price'], name='Gerçek Fiyat', line=dict(color='#00CC96', width=2), fill='tozeroy', fillcolor='rgba(0, 204, 150, 0.1)'))
                fig_main.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['predicted_price'], name='Yapay Zeka', line=dict(dash='dot', color='#AB63FA', width=2)))
                fig_main.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_main, use_container_width=True)

            #  ALT GRAFİKLER
            col_left, col_right = st.columns(2)
            
            with col_left:
                if show_risk:
                    st.subheader(" Volatilite (Bollinger Bantları)")
                    fig_bol = go.Figure()
                    fig_bol.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['Bollinger_Upper'], line=dict(width=0), showlegend=False))
                    fig_bol.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['Bollinger_Lower'], fill='tonexty', fillcolor='rgba(0, 150, 255, 0.1)', line=dict(width=0), name='Bant Aralığı'))
                    fig_bol.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['average_price'], line=dict(color='white', width=1), name='Fiyat'))
                    fig_bol.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig_bol, use_container_width=True)
            
            with col_right:
                if show_momentum:
                    st.subheader(" Momentum (MACD & RSI)")
                    tab_rsi, tab_macd = st.tabs(["RSI", "MACD"])
                    
                    with tab_rsi:
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['RSI'], line=dict(color='#FF6692', width=2)))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                        fig_rsi.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0), yaxis=dict(range=[0, 100]))
                        st.plotly_chart(fig_rsi, use_container_width=True)
                    
                    with tab_macd:
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['MACD'], name='MACD', line=dict(color='#00CC96')))
                        fig_macd.add_trace(go.Scatter(x=df_chart['processed_time'], y=df_chart['Signal_Line'], name='Sinyal', line=dict(color='#EF553B')))
                        fig_macd.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", y=1.1))
                        st.plotly_chart(fig_macd, use_container_width=True)

            #3. DETAY TABLOSU
            with st.expander(" Detaylı Veri Kayıtları"):
                st.dataframe(df_chart.sort_values(by='processed_time', ascending=False).head(50), use_container_width=True)

            time.sleep(1)

            st.rerun()
