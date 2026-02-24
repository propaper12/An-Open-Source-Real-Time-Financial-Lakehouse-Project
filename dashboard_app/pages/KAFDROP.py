import streamlit as st
import json
import time
import random
import pandas as pd
import threading
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import os 
# Sayfa Ayarları
st.set_page_config(page_title="Universal Data Deck", page_icon="🎛️", layout="wide")

st.title("🎛️ Universal Data Ingestion Deck")
st.markdown("---")

# Kafka Ayarları
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = os.getenv("KAFKA_TOPIC_MARKET", "market_data")

# --- SESSION STATE (Hafıza Yönetimi) ---
if 'iot_active' not in st.session_state:
    st.session_state['iot_active'] = False
if 'logs_active' not in st.session_state:
    st.session_state['logs_active'] = False

# VERİ DEPOSU
if 'all_data_storage' not in st.session_state:
    st.session_state['all_data_storage'] = []

# --- 1. BÖLÜM: YAN PANEL (KONTROL & İNDİRME) ---
with st.sidebar:
    st.header("🚀 Veri Simülatörleri")
    
    # IOT SİMÜLASYONU
    st.subheader("🏭 IoT Fabrika Verisi")
    if st.button("IoT Akışını BAŞLAT" if not st.session_state['iot_active'] else "IoT Akışını DURDUR", 
                 type="primary" if not st.session_state['iot_active'] else "secondary"):
        st.session_state['iot_active'] = not st.session_state['iot_active']
    
    if st.session_state['iot_active']:
        st.success("🟢 IoT Sensörleri Aktif")
    
    # SERVER LOG SİMÜLASYONU
    st.subheader("🖥️ Server Logları")
    if st.button("Log Akışını BAŞLAT" if not st.session_state['logs_active'] else "Log Akışını DURDUR"):
        st.session_state['logs_active'] = not st.session_state['logs_active']
        
    st.divider()

    # --- CSV İNDİRME BUTONU ---
    st.header("💾 Veri Seti İşlemleri")
    
    # Veriyi DataFrame'e çevir
    df_download = pd.DataFrame(st.session_state['all_data_storage'])
    
    if not df_download.empty:
        # İndirirken de filtreye saygı duyalım mı? Şimdilik ham veriyi indirsin (Lake mantığı)
        csv = df_download.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tüm Ham Veriyi İndir (CSV)",
            data=csv,
            file_name=f'universal_data_lake_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv',
        )
        st.write(f"📊 Toplam Kayıt: {len(df_download)}")
        
        if st.button("🗑️ Veri Havuzunu Temizle"):
            st.session_state['all_data_storage'] = []
            st.rerun()
    else:
        st.warning("Henüz veri toplanmadı.")

# --- ARKA PLAN İŞLERİ (THREADING) ---
def send_iot_data():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    while st.session_state['iot_active']:
        data = {
            "device_id": f"sensor_{random.randint(1, 5)}",
            "temperature": round(random.uniform(40.0, 90.0), 2),
            "pressure": round(random.uniform(1000, 1050), 2),
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": "IOT"
        }
        producer.send(TOPIC_NAME, value=data)
        time.sleep(1.0) 

def send_log_data():
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    while st.session_state['logs_active']:
        data = {
            "server_ip": f"192.168.1.{random.randint(10, 99)}",
            "level": random.choice(levels),
            "message": "Connection timeout" if random.random() > 0.8 else "Heartbeat OK",
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": "LOGS"
        }
        producer.send(TOPIC_NAME, value=data)
        time.sleep(2)

if st.session_state['iot_active'] and 'iot_thread' not in st.session_state:
    t1 = threading.Thread(target=send_iot_data, daemon=True)
    t1.start()
    st.session_state['iot_thread'] = t1

if st.session_state['logs_active'] and 'log_thread' not in st.session_state:
    t2 = threading.Thread(target=send_log_data, daemon=True)
    t2.start()
    st.session_state['log_thread'] = t2

if not st.session_state['iot_active'] and 'iot_thread' in st.session_state:
    del st.session_state['iot_thread']
if not st.session_state['logs_active'] and 'log_thread' in st.session_state:
    del st.session_state['log_thread']


# --- 2. BÖLÜM: CANLI İZLEME EKRANI ---

col1, col2, col3 = st.columns(3)
with col1:
    filter_type = st.selectbox("Filtrele (Veri Tipi):", ["ALL", "CRYPTO", "IOT", "LOGS"])
with col2:
    auto_refresh = st.checkbox("Canlı Akış", value=True)

placeholder = st.empty()

try:
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='latest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=500
    )
except:
    st.error("Kafka Bağlantısı Kurulamadı!")
    st.stop()

# --- VERİ OKUMA DÖNGÜSÜ ---
while auto_refresh:
    msg_pack = consumer.poll(timeout_ms=200)
    
    for tp, messages in msg_pack.items():
        for msg in messages:
            st.session_state['all_data_storage'].append(msg.value)
    
    full_df = pd.DataFrame(st.session_state['all_data_storage'])
    
    if not full_df.empty:
        # --- FİLTRELEME MANTIĞI ---
        if filter_type != "ALL":
            # Sadece seçilen tipe göre filtrele
            display_df = full_df[full_df['data_type'] == filter_type]
            pool_label = f"📚 Toplam {filter_type} Havuzu"
        else:
            # Hepsini göster
            display_df = full_df
            pool_label = "📚 Toplam Veri Havuzu"

        last_item = display_df.iloc[-1] if not display_df.empty else {}

        with placeholder.container():
            # METRİKLER
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric(pool_label, len(display_df))
            
            # Ekranda gösterilen (Son 50)
            view_count = 50 if len(display_df) > 50 else len(display_df)
            m2.metric("Ekranda Gösterilen", f"Son {view_count}")
            
            m3.metric("Son Veri Tipi", last_item.get('data_type', '-'))
            
            if last_item.get('data_type') == 'IOT':
                m4.metric("🔥 Sıcaklık", f"{last_item.get('temperature')} °C")
            elif last_item.get('data_type') == 'CRYPTO':
                m4.metric("💰 Fiyat", f"${last_item.get('price')}")
            else:
                m4.metric("Durum", "Aktif")

            st.subheader(f"📋 Canlı Veri Akışı ({filter_type})")
            
            # TABLO
            st.dataframe(
                display_df.tail(50).sort_index(ascending=False), 
                use_container_width=True
            )

    time.sleep(0.5)