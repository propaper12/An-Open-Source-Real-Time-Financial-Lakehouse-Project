import time
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# --- 1. AYARLAR ---
# Docker-compose ve .env dosyasından gelen bağlantı bilgileri
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")

print(f"[CONSUMER] Spark Delta Lake Modunda Başlatılıyor (v2.1)...")

# --- 2. MOTORU ÇALIŞTIRMA (SPARK SESSION) ---
# Kütüphane listesine kafka-clients:3.4.0 eklenerek 'NoClassDefFoundError' çözüldü
spark = SparkSession.builder \
    .appName("CryptoMarketLakehouse_Bronze") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.kafka:kafka-clients:3.4.0,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.500,"
            "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.sql.shuffle.partitions", "2") \
    .config("spark.driver.memory", "1g") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# --- 3. ŞEMA TANIMI ---
# Kafka'dan gelen JSON verisinin yapısı
schema = StructType([
    StructField("symbol", StringType()),
    StructField("price", DoubleType()),
    StructField("quantity", DoubleType()),
    StructField("timestamp", StringType())
])

# --- 4. VERİ AKIŞINI BAŞLATMA (KAFKA READ) ---
try:
    # 'earliest' ile Kafka'daki tüm geçmiş verileri MinIO'ya çekiyoruz
    streamingDf = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "market_data") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .option("maxOffsetsPerTrigger", 1000) \
        .load()

    # JSON verisini kolonlara ayırıyoruz
    value_df = streamingDf.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # --- 5. DEPOLAMA (DELTA LAKE WRITE) ---
    # PartitionBy("symbol") ile veriler sembollere göre fiziksel klasörlenir
    # Trigger 10 saniye yapılarak sonuçların MinIO'da hızlı görünmesi sağlandı
    query = value_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .partitionBy("symbol") \
        .option("path", "s3a://market-data/raw_layer_delta") \
        .option("checkpointLocation", "s3a://market-data/checkpoints_delta") \
        .trigger(processingTime='10 seconds') \
        .start()

    print("🚀 Lakehouse Raw (Bronze) Katmanı Dinleniyor...")
    query.awaitTermination()

except Exception as e:
    print(f"🚨 KRİTİK HATA: {e}")
    sys.exit(1)