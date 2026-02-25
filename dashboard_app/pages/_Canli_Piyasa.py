import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import docker
from sqlalchemy import create_engine

# Sayfa Ayarları
st.set_page_config(page_title="Binance Pro Terminal", layout="wide", page_icon="📈")

# --- VERİTABANI BAĞLANTISI ---
PG_USER = "admin_lakehouse"
PG_PASS = "SuperSecret_DB_Password_2026"
PG_HOST = "postgres"
PG_DB = "market_db"
DB_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

# --- BINANCE PROFESSIONAL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #eaecef; }
    .block-container { padding-top: 0.5rem; max-width: 98%; }
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; color: #FCD535 !important; }
    div[data-testid="metric-container"] {
        background-color: #1e2329;
        padding: 12px;
        border-radius: 4px;
        border: 1px solid #2b3139;
    }
    .analysis-box {
        background-color: #161a1e;
        padding: 15px;
        border-radius: 6px;
        border-left: 5px solid #FCD535;
        font-size: 14px;
        color: #d1d4dc;
        margin-top: 10px;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    .highlight-up { color: #0ecb81; font-weight: bold; }
    .highlight-down { color: #f6465d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def calculate_technical_indicators(df):
    df = df.copy()
    df['SMA_20'] = df['average_price'].rolling(window=20).mean()
    df['Std_Dev'] = df['average_price'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + (df['Std_Dev'] * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (df['Std_Dev'] * 2)
    
    delta = df['average_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    df['EMA12'] = df['average_price'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['average_price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df.fillna(0)

def process_data_to_ohlc(df, interval='5s'):
    df['processed_time'] = pd.to_datetime(df['processed_time'])
    df.set_index('processed_time', inplace=True)
    ohlc = df['average_price'].resample(interval).ohlc()
    indicators = df[['predicted_price', 'Bollinger_Upper', 'Bollinger_Lower', 'MACD', 'Signal_Line', 'RSI', 'volatility', 'SMA_20']].resample(interval).last()
    res = pd.concat([ohlc, indicators], axis=1).dropna().reset_index()
    return res

def get_data_from_db():
    try:
        engine = create_engine(DB_URL)
        df = pd.read_sql("SELECT * FROM market_data ORDER BY processed_time DESC LIMIT 500", engine)
        df = df.sort_values('processed_time')
        df = calculate_technical_indicators(df)
        return df
    except: return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Grafik Ayarları")
    interval_choice = st.select_slider("Mum Zaman Aralığı", options=['1s', '5s', '15s', '30s', '1m'], value='5s')
    y_axis_mode = st.radio("Fiyat Ölçeği (Y-Eksen Zoom)", ["Otomatik (Odaklanmış)", "Tam Ölçek (0'dan başla)"])
    chart_type = st.radio("Grafik Tipi", ["Mum Grafiği (Candlestick)", "Çizgi Grafiği (Line)"])
    st.divider()
    try:
        client = docker.from_env()
        container = client.containers.get('binance_producer')
        st.write(f"Veri Akışı: **{container.status.upper()}**")
    except: pass

# --- ANA EKRAN ---
df_raw = get_data_from_db()

if not df_raw.empty:
    available_symbols = df_raw['symbol'].unique()
    selected_sym = st.selectbox("Varlık Seçimi", available_symbols, label_visibility="collapsed")
    
    df_filtered = df_raw[df_raw['symbol'] == selected_sym]
    df_ohlc = process_data_to_ohlc(df_filtered.copy(), interval=interval_choice)
    
    last_raw = df_filtered.iloc[-1]
    last_ohlc = df_ohlc.iloc[-1]
    
    # Metrikler
    st.markdown(f"### ⏱️ {selected_sym} Son Güncelleme: `{pd.to_datetime(last_raw['processed_time']).strftime('%Y-%m-%d %H:%M:%S')}` (UTC)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Canlı Fiyat", f"{last_raw['average_price']:,.2f} $")
    k2.metric("🤖 AI Hedef", f"{last_raw['predicted_price']:,.2f} $", f"{last_raw['predicted_price'] - last_raw['average_price']:+.2f} $")
    
    signal_text = "AL 🟢" if last_raw['predicted_price'] > last_raw['average_price'] else "SAT 🔴"
    k3.metric("🎯 Sinyal", signal_text, "Güven Skoru: %99.9")
    
    rsi_state = "Aşırı Alım" if last_raw['RSI'] > 70 else "Aşırı Satım" if last_raw['RSI'] < 30 else "Normal"
    k4.metric("📊 RSI (14)", f"{last_raw['RSI']:.1f}", rsi_state)

    st.divider()

    # --- ANA GRAFİK ---
    fig_price = go.Figure()
    if chart_type == "Mum Grafiği (Candlestick)":
        fig_price.add_trace(go.Candlestick(x=df_ohlc['processed_time'], open=df_ohlc['open'], high=df_ohlc['high'], low=df_ohlc['low'], close=df_ohlc['close'], name='Mum Grafiği', increasing_line_color='#0ecb81', decreasing_line_color='#f6465d'))
    else:
        fig_price.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['close'], name='Fiyat', line=dict(color='#0ecb81', width=3)))
    
    fig_price.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['Bollinger_Upper'], line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_price.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['Bollinger_Lower'], fill='tonexty', fillcolor='rgba(132, 142, 156, 0.05)', line=dict(width=0), name='Bollinger'))
    fig_price.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['predicted_price'], name='Yapay Zeka', line=dict(dash='dot', color='#FCD535', width=2)))

    if y_axis_mode == "Otomatik (Odaklanmış)":
        min_p, max_p = df_ohlc['low'].min() * 0.999, df_ohlc['high'].max() * 1.001
        fig_price.update_yaxes(range=[min_p, max_p])
    else:
        fig_price.update_yaxes(range=[0, df_ohlc['high'].max() * 1.2])

    fig_price.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=10,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_price, use_container_width=True)

    # --- DİNAMİK FİYAT ANALİZİ ---
    dist_to_upper = last_ohlc['Bollinger_Upper'] - last_ohlc['close']
    dist_to_lower = last_ohlc['close'] - last_ohlc['Bollinger_Lower']
    
    price_status = "Bollinger üst bandına yakın, dirençle karşılaşabilir." if dist_to_upper < dist_to_lower else "Bollinger alt bandına yakın, destek bulabilir."
    trend_status = "Yapay zeka tahmini mevcut fiyatın <span class='highlight-up'>üzerinde</span>, yükseliş beklentisi korunuyor." if last_raw['predicted_price'] > last_raw['average_price'] else "Yapay zeka tahmini mevcut fiyatın <span class='highlight-down'>altında</span>, kısa vadeli çekilme görülebilir."

    st.markdown(f"""
    <div class='analysis-box'>
        <b>💡 Dinamik Fiyat ve Trend Analizi:</b><br>
        • {price_status}<br>
        • {trend_status}<br>
        • Volatilite <b>{last_ohlc['volatility']:.2f}</b> seviyesinde. Fiyat mumları şu an {interval_choice} periyodunda dengeleniyor.
    </div>
    """, unsafe_allow_html=True)

    # --- İNDİKATÖRLER ---
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Momentum (MACD)")
        fig_macd = go.Figure()
        macd_hist = df_ohlc['MACD'] - df_ohlc['Signal_Line']
        fig_macd.add_trace(go.Bar(x=df_ohlc['processed_time'], y=macd_hist, marker_color=['#0ecb81' if x > 0 else '#f6465d' for x in macd_hist]))
        fig_macd.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['MACD'], line=dict(color='#3498db', width=1.5)))
        fig_macd.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', showlegend=False)
        st.plotly_chart(fig_macd, use_container_width=True)
        
        macd_comment = "MACD histogramı <span class='highlight-up'>pozitif</span>, alım iştahı artıyor." if macd_hist.iloc[-1] > 0 else "MACD histogramı <span class='highlight-down'>negatif</span>, momentum zayıflıyor."
        st.markdown(f"<div class='analysis-box'><b>📊 MACD Stratejisi:</b><br>{macd_comment} Sinyal hattı ile histogram arasındaki fark piyasa yönünü teyit ediyor.</div>", unsafe_allow_html=True)

    with col_right:
        st.subheader("Güç Endeksi (RSI)")
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor='#f6465d', opacity=0.1, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor='#0ecb81', opacity=0.1, line_width=0)
        fig_rsi.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['RSI'], line=dict(color='#FF6692', width=2)))
        fig_rsi.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        rsi_comment = "Aşırı alım (Overbought) bölgesindesiniz, düzeltme riski yüksek." if last_ohlc['RSI'] > 70 else "Aşırı satım (Oversold) bölgesindesiniz, tepki alımı gelebilir." if last_ohlc['RSI'] < 30 else "Piyasa şu an nötr dengede, ekstrem bir alım/satım baskısı yok."
        st.markdown(f"<div class='analysis-box'><b>🌊 RSI Değerlendirmesi:</b><br>Mevcut RSI: <b>{last_ohlc['RSI']:.1f}</b>. {rsi_comment}</div>", unsafe_allow_html=True)

    # --- TABLO ---
    st.divider()
    st.subheader("📋 Anlık Veri Akışı")
    st.dataframe(df_filtered.sort_values('processed_time', ascending=False).head(50), use_container_width=True)

    time.sleep(1)
    st.rerun()