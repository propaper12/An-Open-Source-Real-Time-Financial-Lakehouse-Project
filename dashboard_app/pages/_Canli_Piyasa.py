import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json
import os
from datetime import datetime
from kafka import KafkaConsumer
from sqlalchemy import create_engine

# ==========================================
# 0. SAYFA KONFİGÜRASYONU
# ==========================================
st.set_page_config(page_title="Enterprise Trading Terminal", layout="wide", page_icon="📈")

# ==========================================
# 1. BAĞLANTI VE ALTYAPI AYARLARI
# ==========================================
PG_USER = "admin_lakehouse"
PG_PASS = "SuperSecret_DB_Password_2026"
PG_HOST = "postgres"
PG_DB = "market_db"
DB_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# ==========================================
# 2. KURUMSAL UI/UX TASARIMI (CSS)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #eaecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .block-container { padding-top: 2rem; max-width: 95%; }
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: bold; color: #FCD535 !important; }
    div[data-testid="metric-container"] { background-color: #1e2329; padding: 15px; border-radius: 6px; border: 1px solid #2b3139; }
    .analysis-box { background-color: #161a1e; padding: 15px; border-radius: 6px; border-left: 5px solid #FCD535; font-size: 15px; color: #d1d4dc; margin-top: 10px; margin-bottom: 20px; line-height: 1.6; }
    .highlight-up { color: #0ecb81; font-weight: bold; }
    .highlight-down { color: #f6465d; font-weight: bold; }
    .live-indicator { color: #f6465d; font-weight: bold; animation: blinker 1.5s linear infinite; font-size: 18px; margin-right: 10px;}
    .live-clock { color: #848E9C; font-size: 20px; font-weight: bold; font-family: 'Courier New', Courier, monospace; background-color: #1e2329; padding: 5px 15px; border-radius: 4px; border: 1px solid #2b3139;}
    @keyframes blinker { 50% { opacity: 0; } }
    div[data-baseweb="select"] { font-size: 18px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ İŞLEME VE İNDİKATÖR FONKSİYONLARI
# ==========================================
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
    
    # Premium Verilerin Çökmemesi İçin Güvenlik Kontrolü
    base_cols = ['predicted_price', 'Bollinger_Upper', 'Bollinger_Lower', 'MACD', 'Signal_Line', 'RSI', 'volatility', 'SMA_20']
    premium_cols = [c for c in ['trade_side', 'is_buyer_maker'] if c in df.columns]
    
    indicators = df[base_cols + premium_cols].resample(interval).last()
    
    # Yeni Hacim (Volume) Verisini Toplama (Sum)
    if 'volume_usd' in df.columns:
        ohlc['volume_usd_sum'] = df['volume_usd'].resample(interval).sum()
        
    return pd.concat([ohlc, indicators], axis=1).dropna().reset_index()

# ==========================================
# 4. DUAL-TRACK MİMARİSİ (FAST PATH & SLOW PATH)
# ==========================================
@st.cache_data(ttl=5, show_spinner=False)
def get_data_from_db():
    try:
        engine = create_engine(DB_URL)
        df = pd.read_sql("SELECT * FROM market_data ORDER BY processed_time DESC LIMIT 1000", engine)
        if not df.empty:
            df = df.sort_values('processed_time')
            df = df.groupby('symbol').apply(calculate_technical_indicators).reset_index(drop=True)
        return df
    except: return pd.DataFrame()

if 'kafka_consumer' not in st.session_state:
    try:
        st.session_state['kafka_consumer'] = KafkaConsumer(
            'market_data', bootstrap_servers=KAFKA_SERVER, auto_offset_reset='latest',
            enable_auto_commit=False, value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=50
        )
    except: st.session_state['kafka_consumer'] = None

def get_live_price(symbol):
    live_p = None
    if st.session_state['kafka_consumer']:
        try:
            msg_pack = st.session_state['kafka_consumer'].poll(timeout_ms=50)
            for tp, messages in msg_pack.items():
                for msg in messages:
                    if msg.value.get('symbol') == symbol: live_p = float(msg.value.get('price'))
        except: pass
    return live_p

# ==========================================
# 5. UI STATE YÖNETİMİ
# ==========================================
if 'selected_coin' not in st.session_state: st.session_state['selected_coin'] = None
if 'refresh_counter' not in st.session_state: st.session_state['refresh_counter'] = 5

# ==========================================
# 6. YAN PANEL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9676/9676527.png", width=60)
    st.header("⚙️ Ayarlar")
    interval_choice = st.select_slider("Mum Zaman Aralığı", options=['1s', '5s', '15s', '30s', '1m'], value='5s')
    y_axis_mode = st.radio("Y-Eksen Fiyat Ölçeği", ["Odaklanmış (Zoom)", "Tam Ölçek"])
    chart_type = st.radio("Grafik Tipi", ["Candlestick (Mum)", "Line (Çizgi)"])
    st.divider()
    
    st.write("🔄 Yapay Zeka Güncellemesi:")
    progress_bar = st.progress(st.session_state['refresh_counter'] / 5.0)
    st.caption(f"Kalan: {st.session_state['refresh_counter']} saniye")

# ==========================================
# 7. ANA EKRAN DÜZENİ
# ==========================================
df_raw = get_data_from_db()

if not df_raw.empty:
    available_symbols = sorted(df_raw['symbol'].unique())
    if st.session_state['selected_coin'] not in available_symbols:
        st.session_state['selected_coin'] = available_symbols[0]
    
    c_head1, c_head2 = st.columns([1, 1])
    with c_head1:
        selected_sym = st.selectbox("🪙 İZLENEN VARLIK", available_symbols, index=available_symbols.index(st.session_state['selected_coin']))
        st.session_state['selected_coin'] = selected_sym
    with c_head2:
        current_time_str = datetime.now().strftime("%d %b %Y - %H:%M:%S")
        st.markdown(f"<div style='text-align: right; margin-top: 30px;'><span class='live-indicator'>● CANLI YAYIN</span> <span class='live-clock'>🕒 {current_time_str}</span></div>", unsafe_allow_html=True)

    df_filtered = df_raw[df_raw['symbol'] == selected_sym]
    
    if not df_filtered.empty:
        df_ohlc = process_data_to_ohlc(df_filtered.copy(), interval=interval_choice)
        last_raw = df_filtered.iloc[-1]
        last_ohlc = df_ohlc.iloc[-1] if not df_ohlc.empty else last_raw
        
        live_price = get_live_price(selected_sym)
        display_price = live_price if live_price else last_raw['average_price']
        
        # --- ÜST METRİKLER (ORİJİNAL) ---
        st.write("") 
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Anlık Fiyat (Kafka)", f"{display_price:,.5f} $")
        k2.metric("🤖 Yapay Zeka Hedefi", f"{last_raw['predicted_price']:,.5f} $", f"{last_raw['predicted_price'] - display_price:+.5f} $")
        
        signal = "AL 🟢" if last_raw['predicted_price'] > display_price else "SAT 🔴"
        k3.metric("🎯 Sistem Sinyali", signal)
        
        rsi_val = last_raw['RSI']
        rsi_state = "Aşırı Alım" if rsi_val > 70 else "Aşırı Satım" if rsi_val < 30 else "Nötr"
        k4.metric("📊 RSI (14)", f"{rsi_val:.1f}", rsi_state)

        # --- YENİ PREMIUM METRİKLER (ORİJİNAL TASARIMA UYGUN) ---
        if 'volume_usd' in df_filtered.columns:
            st.write("")
            p1, p2, p3 = st.columns(3)
            vol_usd = last_raw.get('volume_usd', 0)
            p1.metric("🌊 Son İşlem Hacmi (USD)", f"${vol_usd:,.0f}")

            side_val = last_raw.get('trade_side', 'N/A')
            side_color = "🟢 ALICI (BUY)" if side_val == 'BUY' else "🔴 SATICI (SELL)" if side_val == 'SELL' else "⚪ NÖTR"
            p2.metric("⚖️ Son İşlem Yönü", side_color)

            is_maker = last_raw.get('is_buyer_maker', False)
            maker_text = "Satıcı Agresif" if is_maker else "Alıcı Agresif"
            p3.metric("🔥 Piyasa Baskısı", maker_text)

        st.divider()

        # ==========================================
        # 8. ANA FİYAT GRAFİĞİ VE YORUMU (ORİJİNAL)
        # ==========================================
        st.markdown(f"<h3 style='color: #eaecef;'>Fiyat ve Bollinger Bantları ({interval_choice})</h3>", unsafe_allow_html=True)
        if not df_ohlc.empty:
            fig = go.Figure()
            if chart_type == "Candlestick (Mum)":
                fig.add_trace(go.Candlestick(x=df_ohlc['processed_time'], open=df_ohlc['open'], high=df_ohlc['high'], low=df_ohlc['low'], close=df_ohlc['close'], name='Mum', increasing_line_color='#0ecb81', decreasing_line_color='#f6465d'))
            else:
                fig.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['close'], name='Fiyat', line=dict(color='#0ecb81', width=3)))
            
            fig.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['Bollinger_Upper'], line=dict(width=0), showlegend=False, hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['Bollinger_Lower'], fill='tonexty', fillcolor='rgba(132, 142, 156, 0.05)', line=dict(width=0), name='Bollinger Bandı'))
            fig.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['predicted_price'], name='AI Tahmini', line=dict(dash='dot', color='#FCD535', width=2)))

            if y_axis_mode == "Odaklanmış (Zoom)":
                fig.update_yaxes(range=[df_ohlc['low'].min() * 0.999, df_ohlc['high'].max() * 1.001])
            
            fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=10,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # ANA GRAFİK CANLI YORUM KUTUSU
        dist_up = last_ohlc['Bollinger_Upper'] - last_ohlc['close']
        dist_down = last_ohlc['close'] - last_ohlc['Bollinger_Lower']
        p_status = "Bollinger üst bandına (Direnç) yaklaşıyor, satış baskısı artabilir." if dist_up < dist_down else "Bollinger alt bandına (Destek) yakın, tepki alımı gelebilir."
        t_status = f"Yapay zeka tahmini mevcut fiyatın <span class='highlight-{'up' if last_raw['predicted_price'] > last_raw['average_price'] else 'down'}'>{'üzerinde (Yükseliş Beklentisi)' if last_raw['predicted_price'] > last_raw['average_price'] else 'altında (Düşüş Beklentisi)'}</span>."
        
        st.markdown(f"<div class='analysis-box'><b>💡 Dinamik Fiyat ve Trend Analizi:</b><br>• {p_status}<br>• {t_status}</div>", unsafe_allow_html=True)

        # ==========================================
        # 9. ALT GRAFİKLER (MACD & RSI) VE YORUMLARI
        # ==========================================
        if not df_ohlc.empty:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("<h4 style='color: #848E9C;'>Momentum (MACD)</h4>", unsafe_allow_html=True)
                fig_macd = go.Figure()
                macd_hist = df_ohlc['MACD'] - df_ohlc['Signal_Line']
                fig_macd.add_trace(go.Bar(x=df_ohlc['processed_time'], y=macd_hist, marker_color=['#0ecb81' if x > 0 else '#f6465d' for x in macd_hist]))
                fig_macd.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['MACD'], line=dict(color='#3498db', width=1.5)))
                fig_macd.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', showlegend=False)
                st.plotly_chart(fig_macd, use_container_width=True)
                
                macd_val = macd_hist.iloc[-1]
                macd_comment = "MACD histogramı <span class='highlight-up'>pozitif</span> bölgede, alıcılar güçleniyor." if macd_val > 0 else "MACD histogramı <span class='highlight-down'>negatif</span> bölgede, satıcılar baskın."
                st.markdown(f"<div class='analysis-box'><b>📊 MACD Stratejisi:</b><br>{macd_comment}</div>", unsafe_allow_html=True)

            with col_right:
                st.markdown("<h4 style='color: #848E9C;'>Güç Endeksi (RSI)</h4>", unsafe_allow_html=True)
                fig_rsi = go.Figure()
                fig_rsi.add_hrect(y0=70, y1=100, fillcolor='#f6465d', opacity=0.1, line_width=0)
                fig_rsi.add_hrect(y0=0, y1=30, fillcolor='#0ecb81', opacity=0.1, line_width=0)
                fig_rsi.add_trace(go.Scatter(x=df_ohlc['processed_time'], y=df_ohlc['RSI'], line=dict(color='#FF6692', width=2)))
                fig_rsi.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_rsi, use_container_width=True)
                
                rsi_comment = "Fiyat <span class='highlight-down'>aşırı alım (Overbought)</span> bölgesinde. Düzeltme riski masada." if rsi_val > 70 else "Fiyat <span class='highlight-up'>aşırı satım (Oversold)</span> bölgesinde. Dip arayışı olabilir." if rsi_val < 30 else "Piyasa şu an nötr dengede, ekstrem bir alım/satım baskısı yok."
                st.markdown(f"<div class='analysis-box'><b>🌊 RSI Değerlendirmesi:</b><br>Mevcut RSI: <b>{rsi_val:.1f}</b>. {rsi_comment}</div>", unsafe_allow_html=True)

        # ==========================================
        # 10. YENİ EKLENEN: HACİM (VOLUME) GRAFİĞİ VE YORUMU
        # ==========================================
        if 'volume_usd_sum' in df_ohlc.columns and not df_ohlc.empty:
            st.markdown("<h4 style='color: #848E9C;'>İşlem Hacmi (Volume USD)</h4>", unsafe_allow_html=True)
            fig_vol = go.Figure()
            colors = ['#0ecb81' if row['close'] >= row['open'] else '#f6465d' for index, row in df_ohlc.iterrows()]
            fig_vol.add_trace(go.Bar(x=df_ohlc['processed_time'], y=df_ohlc['volume_usd_sum'], marker_color=colors))
            fig_vol.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#0b0e11', paper_bgcolor='#0b0e11', showlegend=False)
            st.plotly_chart(fig_vol, use_container_width=True)

            last_vol = df_ohlc['volume_usd_sum'].iloc[-1]
            trade_side = last_raw.get('trade_side', 'Bilinmiyor')
            vol_trend = "alıcıların kontrolünde" if trade_side == 'BUY' else "satıcıların kontrolünde"
            vol_comment = f"Son periyotta piyasada <b>${last_vol:,.0f}</b> hacim döndü. Ağırlıklı emir akışı <span class='highlight-{'up' if trade_side == 'BUY' else 'down'}'>{vol_trend}</span> ilerliyor."
            st.markdown(f"<div class='analysis-box'><b>🔥 Hacim ve Emir Akışı (Order Flow) Analizi:</b><br>{vol_comment}</div>", unsafe_allow_html=True)

        # ==========================================
        # 11. POSTGRESQL HAM VERİ TABLOSU
        # ==========================================
        st.divider()
        st.subheader("📋 PostgreSQL Veri Katmanı (Son 10 İşlem Kaydı)")
        
        display_cols = ['processed_time', 'symbol', 'average_price', 'predicted_price', 'trade_side', 'is_buyer_maker', 'volume_usd', 'volatility', 'RSI', 'MACD', 'Bollinger_Upper', 'Bollinger_Lower']
        available_cols = [c for c in display_cols if c in df_filtered.columns]
        
        st.dataframe(
            df_filtered[available_cols].sort_values('processed_time', ascending=False).head(10).style.format({
                'average_price': '{:.5f}', 'predicted_price': '{:.5f}', 'volatility': '{:.4f}', 
                'volume_usd': '${:,.2f}',
                'RSI': '{:.2f}', 'MACD': '{:.4f}', 'Bollinger_Upper': '{:.2f}', 'Bollinger_Lower': '{:.2f}'
            }), 
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# 12. SAYAÇ YÖNETİMİ VE RERUN (LOOP)
# ==========================================
time.sleep(1)
st.session_state['refresh_counter'] -= 1

if st.session_state['refresh_counter'] <= 0:
    st.session_state['refresh_counter'] = 5 
    
st.rerun()