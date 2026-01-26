import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "admin")

def get_connection():
    return psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)

def run_query(query):
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def execute_command(command):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
    finally:
        conn.close()

def render_postgres_tab():
    st.subheader(" SQL Studio (PostgreSQL)")
    
    default_query = "SELECT * FROM market_data ORDER BY processed_time DESC LIMIT 10;"
    query = st.text_area("SQL Sorgusu", value=default_query, height=150)
    
    if st.button(" Çalıştır"):
        try:
            df = run_query(query)
            st.success(f"Sorgu Başarılı! ({len(df)} satır döndü)")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Hatası: {e}")

    st.divider()
    
    st.markdown("### Hızlı İşlemler (Macro)")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button(" Tabloları Listele"):
            try:
                df = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                st.table(df)
            except Exception as e: st.error(e)

    with c2:
        if st.button(" Kayıt Sayısı (Count)"):
            try:
                df = run_query("SELECT COUNT(*) FROM market_data;")
                count = df.iloc[0,0]
                st.metric("Toplam Veri", f"{count:,}")
            except Exception as e: st.error(e)
            
    with c3:
        if st.button(" Tabloyu Temizle (TRUNCATE)"):
            try:
                execute_command("TRUNCATE TABLE market_data;")
                st.success("Tablo sıfırlandı! Veriler silindi.")
            except Exception as e: st.error(e)