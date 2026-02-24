# batch_processor.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import os
import sys
import re

# --- AYARLAR (.env'den dinamik olarak çekilir) ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")

# Türkçe karakter düzeltme haritası
TR_CHARS = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', 
            'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'}

def clean_column_name(col_name):
    """Sütun isimlerini veritabanı dostu hale getirir"""
    for tr, en in TR_CHARS.items():
        col_name = col_name.replace(tr, en)
    clean = re.sub(r'[^a-zA-Z0-9]', '_', col_name.strip())
    return clean.lower()

def process_batch_file(filename):
    print(f" Dinamik Batch İşlemi: {filename}")

    spark = SparkSession.builder \
        .appName("UniversalBatchProcessor") \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

    input_path = f"s3a://market-data/raw_batch_uploads/{filename}"

    try:
        # 1. CSV'yi Oku 
        df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
        
        # 2. Sütun İsimlerini Temizle 
        cleaned_columns = [clean_column_name(c) for c in df.columns]
        df_clean = df.toDF(*cleaned_columns)

        # 3. Tablo İsmi Üretme
        clean_filename = clean_column_name(filename.split('.')[0])
        table_name = f"upload_{clean_filename}"

        print(f" Hedef Tablo Adı: {table_name}")
        
        # 4. Veriyi Kaydet (PostgreSQL + MinIO)
        
        # MinIO (Parquet olarak yedekle)
        minio_path = f"s3a://market-data/batch_processed/{table_name}"
        df_clean.write.format("parquet").mode("overwrite").save(minio_path)
        print(f" MinIO'ya yedeklendi: {minio_path}")

        # PostgreSQL (Metabase için) - Şifreler Dinamik!
        jdbc_url = f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}"
        db_properties = {
            "user": PG_USER,
            "password": PG_PASS,
            "driver": "org.postgresql.Driver"
        }
        
        df_clean.write.jdbc(url=jdbc_url, table=table_name, mode="overwrite", properties=db_properties)
        
        print(f"PostgreSQL'e tablo olarak yazıldı: {table_name}")
        print(" İşlem Tamamlandı.")

    except Exception as e:
        print(f" Hata oluştu: {e}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        process_batch_file(fname)
    else:
        print("Dosya adı eksik.")