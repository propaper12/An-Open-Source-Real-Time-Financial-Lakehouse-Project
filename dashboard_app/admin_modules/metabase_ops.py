import streamlit as st
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

load_dotenv()

def render_metabase_tab():
    st.subheader(" Metabase Dashboard")
    
    METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3005")
    
    st.markdown(f" **[Metabase'i Yeni Sekmede Aç]({METABASE_URL})**")
    st.warning("Eğer görüntü gelmiyorsa Metabase ayarlarından 'Embedding' iznini açın.")
    
    try:
        components.iframe(METABASE_URL, height=800, scrolling=True)
    except Exception as e:
        st.error(f"Hata: {e}")