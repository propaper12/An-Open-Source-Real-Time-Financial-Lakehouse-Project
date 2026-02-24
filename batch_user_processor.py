# batch_user_processor.py
from pyspark.sql import SparkSession
import os

# Ayarları .env'den çek
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")

# Spark Oturumu (Şifreler dinamik)
spark = SparkSession.builder \
    .appName("UserBatchProcessor") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

path = "s3a://market-data/user_uploads/*.csv"
df = spark.read.option("header", "true").option("inferSchema", "true").csv(path)

processed_df = df.dropna().distinct()

processed_df.write.format("delta").mode("overwrite").save("s3a://market-data/gold_user_analytics")

print("Kullanıcı verisi başarıyla işlendi ve Gold katmanına yazıldı!")
spark.stop()