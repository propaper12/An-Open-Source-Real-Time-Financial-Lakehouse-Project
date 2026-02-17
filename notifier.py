# Dosya: notifier.py
import psycopg2
import os
import datetime

# DB Ayarları (Docker içinden erişim için host='postgres')
DB_HOST = "postgres"
DB_NAME = "market_db"
DB_USER = "admin"
DB_PASS = "admin"

def send_alert(title, message, status="INFO", source="System"):
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        full_msg = f"[{title}] {message}"
        cur.execute(
            "INSERT INTO system_alerts (level, source, message, created_at) VALUES (%s, %s, %s, %s)",
            (status, source, full_msg, datetime.datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DB Log Hatası: {e}")