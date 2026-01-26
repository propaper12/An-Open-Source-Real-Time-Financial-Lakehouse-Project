import streamlit as st
import subprocess
import os
import signal
import time

LOG_FILE = "/app/producer_activity.log"

if 'active_stream_pid' not in st.session_state:
    st.session_state['active_stream_pid'] = None
    st.session_state['active_source'] = None

st.set_page_config(page_title="Universal Connector", layout="wide")
st.header("🔌 Universal Data Gateway")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(" Kaynak Yapılandırması")
    st.info("Bu kapıdan içeri giren her veri, sistem tarafından otomatik olarak normalize edilir ve saklanır.")
    
    source_type_selection = st.selectbox(
        "Veri Tipi Seçin veya Yazın", 
        ["Borsa / Finans", "IoT Sensor (Isı/Nem)", "Server (CPU/RAM)", "Web Trafiği", "Enerji Tüketimi", "Özel Tanımlı..."]
    )
    
    final_source_type = source_type_selection
    if source_type_selection == "Özel Tanımlı...":
        final_source_type = st.text_input("Veri Tipi Adı", value="Fabrika_Uretim_Hizi")
    
    source_id = st.text_input("Benzersiz ID (Symbol/DeviceID)", value="DATA_SOURCE_001")

    st.markdown("---")

    if st.session_state['active_stream_pid'] is None:
        if st.button(" AKIŞI BAŞLAT", type="primary", use_container_width=True):
            # Temizlik
            if os.path.exists(LOG_FILE):
                try: os.remove(LOG_FILE)
                except: pass
            
            with open(LOG_FILE, 'w') as fp:
                fp.write(" Universal bağlantı kuruluyor...\n")

            process = subprocess.Popen(
                ["python", "-u", "/app/universal_producer.py", final_source_type, source_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            st.session_state['active_stream_pid'] = process.pid
            st.session_state['active_source'] = f"{final_source_type} -> {source_id}"
            st.rerun()
    else:
        st.success(" Veri Hattı Aktif")
        st.write(f" Kaynak: **{st.session_state['active_source']}**")
        
        if st.button(" BAĞLANTIYI KES", type="secondary", use_container_width=True):
            try:
                os.kill(st.session_state['active_stream_pid'], signal.SIGTERM)
            except:
                pass
            st.session_state['active_stream_pid'] = None
            st.session_state['active_source'] = None
            st.rerun()

with col2:
    st.subheader(" Gelen Veri Paketleri (Canlı)")
    
    terminal = st.empty()
    
    if st.session_state['active_stream_pid']:
        if os.path.exists(LOG_FILE):
             with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-15:]
                terminal.code("".join(lines), language="cmd")
        time.sleep(1)
        st.rerun()
    else:
        terminal.code("🛑 Hat kapalı. Veri akışı bekleniyor...", language="bash")