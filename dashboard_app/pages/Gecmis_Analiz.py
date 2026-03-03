import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from deltalake import DeltaTable
import os

# --- 0. SAYFA AYARLARI ---
st.set_page_config(page_title="Pro Terminal | Geçmiş Analitik", layout="wide", page_icon="📈")

# --- 1. KURUMSAL CSS (Binance Style) ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #eaecef; }
    .metric-card { background-color: #1e2329; padding: 20px; border-radius: 10px; border: 1px solid #2b3139; text-align: center; }
    .metric-value { font-size: 24px; font-weight: bold; color: #FCD535; }
    .metric-label { font-size: 12px; color: #848E9C; text-transform: uppercase; }
    .trader-note { background-color: #161a1e; padding: 15px; border-radius: 8px; border-left: 4px solid #FCD535; font-size: 14px; margin-bottom: 20px; color: #d1d4dc; }
    h1, h2, h3 { color: #FCD535 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. S3 & STORAGE OPTIONS ---
storage_options = {
    "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER", "admin"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
    "AWS_ENDPOINT_URL": os.getenv("MINIO_ENDPOINT", "http://minio:9000"), 
    "AWS_REGION": "us-east-1",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    "AWS_ALLOW_HTTP": "true"
}

# --- 3. TEKNİK GÖSTERGE HESAPLAMALARI ---
def add_indicators(df):
    # Moving Averages
    df['MA7'] = df['close'].rolling(window=7).mean()
    df['MA25'] = df['close'].rolling(window=25).mean()
    df['MA99'] = df['close'].rolling(window=99).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_mid'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_mid'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_mid'] - (df['BB_std'] * 2)
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    
    return df

# --- 4. OPTİMİZE VERİ YÜKLEME ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_full_batch_data(interval):
    path = "s3://market-data/historical_daily_delta" if interval == "Günlük" else "s3://market-data/historical_hourly_delta"
    try:
        dt = DeltaTable(path, storage_options=storage_options)
        return dt.to_pandas()
    except: return pd.DataFrame()

# --- 5. YAN PANEL ---
with st.sidebar:
    st.header("📊 Terminal Ayarları")
    interval = st.radio("Zaman Dilimi", ["Günlük", "Saatlik"])
    all_data = load_full_batch_data(interval)
    
    if not all_data.empty:
        coin_list = sorted(all_data['symbol'].unique())
        selected_coin = st.selectbox("Varlık Seç", coin_list)
        df = all_data[all_data['symbol'] == selected_sym if 'selected_sym' in locals() else all_data['symbol'] == selected_coin].copy()
    else:
        st.error("Veri Yüklenemedi!")
        st.stop()

# --- 6. İŞLEME ---
df = df.sort_values("timestamp")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = add_indicators(df)

# --- 7. ANA EKRAN ---
st.title(f"🚀 {selected_coin} Professional Quantitative Terminal")

# Üst Özet Kartları
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-label'>Güncel Fiyat</div><div class='metric-value'>${df['close'].iloc[-1]:,.2f}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-label'>RSI (14)</div><div class='metric-value'>{df['RSI'].iloc[-1]:.2f}</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-label'>24s Hacim</div><div class='metric-value'>${df['volume'].iloc[-1]/1e6:.2f}M</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='metric-card'><div class='metric-label'>Trend Gücü</div><div class='metric-value'>{'BOĞA' if df['close'].iloc[-1] > df['MA99'].iloc[-1] else 'AYI'}</div></div>", unsafe_allow_html=True)

# 1. ANA TEKNİK GRAFİK (OHLC + MA + BB + Volume + MACD)
st.subheader("🛠️ Gelişmiş Teknik Analiz Paneli")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, 
                    row_width=[0.2, 0.2, 0.6], subplot_titles=("", "Hacim", "MACD"))

# Candlestick & Bollinger
fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Fiyat'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BB_upper'], line=dict(color='rgba(173, 216, 230, 0.2)'), name='BB Üst'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BB_lower'], line=dict(color='rgba(173, 216, 230, 0.2)'), fill='tonexty', name='BB Alt'), row=1, col=1)

# MAs
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA7'], line=dict(color='#fcd535', width=1), name='MA7'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA25'], line=dict(color='#e84118', width=1), name='MA25'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA99'], line=dict(color='#3498db', width=1.5), name='MA99'), row=1, col=1)

# Volume
colors = ['#f6465d' if row['open'] > row['close'] else '#0ecb81' for index, row in df.iterrows()]
fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], marker_color=colors, name='Hacim'), row=2, col=1)

# MACD
fig.add_trace(go.Bar(x=df['timestamp'], y=df['MACD_Hist'], name='MACD Hist'), row=3, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD'], line=dict(color='#00d2ff'), name='MACD'), row=3, col=1)
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['Signal'], line=dict(color='#ff9ff3'), name='Sinyal'), row=3, col=1)

fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False, margin=dict(t=30))
st.plotly_chart(fig, use_container_width=True)

st.markdown("""<div class='trader-note'><b>💡 Trader Notu:</b> Bu grafik Binance Pro arayüzüne sadık kalınarak tasarlanmıştır. 
MA99 (Mavi Çizgi) uzun vadeli ana trendi gösterir. Fiyat Bollinger Bantlarının dışına çıktığında 'Aşırı Alım' veya 'Aşırı Satım' sinyali olarak değerlendirilir.</div>""", unsafe_allow_html=True)

# 2. ISİ HARİTASI VE KORELASYON
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Mevsimsellik: Günlük Getiri (%)")
    df['weekday'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month_name()
    pivot = df.pivot_table(index='month', columns='weekday', values='returns', aggfunc='mean') * 100
    fig_hm = px.imshow(pivot, color_continuous_scale='RdYlGn', text_auto=".2f")
    fig_hm.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_hm, use_container_width=True)
    st.caption("Hangi aylarda ve günlerde varlığın tarihsel olarak daha iyi performans gösterdiğini izleyin.")

with col2:
    st.subheader("🔗 Batch Korelasyon Analizi")
    # Batch içindeki diğer coinlerle korelasyon
    corr_df = all_data.pivot(index='timestamp', columns='symbol', values='close').pct_change().corr()
    fig_corr = px.imshow(corr_df, color_continuous_scale='Viridis', text_auto=".2f")
    fig_corr.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_corr, use_container_width=True)
    st.caption("Seçilen varlığın diğer coinlerle ne kadar benzer hareket ettiğini (Beta) analiz eder.")

# 3. RSI VE VOLATİLİTE
cola, colb = st.columns(2)

with cola:
    st.subheader("🌡️ Göreceli Güç Endeksi (RSI)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI'], line=dict(color='#FCD535')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#f6465d")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#0ecb81")
    fig_rsi.update_layout(template="plotly_dark", height=300, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_rsi, use_container_width=True)
    st.markdown("<div class='trader-note'>RSI 70 üzeri 'Aşırı Şişkinlik', 30 altı 'Aşırı Ucuzluk' bölgesidir.</div>", unsafe_allow_html=True)

with colb:
    st.subheader("📉 Maksimum Kayıp (Drawdown)")
    rolling_max = df['close'].cummax()
    drawdown = (df['close'] - rolling_max) / rolling_max
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=df['timestamp'], y=drawdown*100, fill='tozeroy', line=dict(color='#f6465d')))
    fig_dd.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_dd, use_container_width=True)
    st.caption("Tarihi zirvesinden olan düşüş yüzdesi.")

# 4. TABLO VERİSİ
st.subheader("📝 Ham Veri Kayıtları (Batch Layer)")
st.dataframe(df.sort_values("timestamp", ascending=False).head(100), use_container_width=True)