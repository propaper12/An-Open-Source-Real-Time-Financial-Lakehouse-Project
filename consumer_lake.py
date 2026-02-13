import time
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
# Şema importlarını azalttık çünkü artık ham veri saklıyoruz

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")

print(f"[CONSUMER] Generic Raw Data Ingestion Başlatılıyor...")

spark = SparkSession.builder \
    .appName("GenericBronzeIngestion") \
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
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

try:
    # 1. Kafka'dan Oku (Ham binary olarak)
    streamingDf = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "market_data") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .option("maxOffsetsPerTrigger", 1000) \
        .load()

    # 2. "APTAL" TÜKETİCİ MANTIĞI (Dumb Consumer)
    # Veriyi açıp içine bakma. Olduğu gibi string'e çevir ve sakla.
    # Böylece IoT, Log, Crypto ne gelirse gelsin bozulmadan saklanır.
    raw_df = streamingDf.select(
        col("key").cast("string").alias("kafka_key"),
        col("value").cast("string").alias("raw_payload"), # <-- Bütün veri burada JSON String olarak duracak
        col("timestamp").alias("ingest_time")
    )

    # 3. Bronze Katmanına Yaz (Delta Lake)
    # Not: partitionBy("symbol") KALDIRILDI çünkü symbol sütunu artık JSON içinde gizli.
    # Bronze katmanı ham ve hızlı olmalı.
    query = raw_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("path", "s3a://market-data/raw_layer_delta") \
        .option("checkpointLocation", "s3a://market-data/checkpoints_delta_raw") \
        .trigger(processingTime='5 seconds') \
        .start()

    print(" Lakehouse Raw (Bronze) Katmanı: Her türlü veriyi kabul ediyor...")
    query.awaitTermination()

except Exception as e:
    print(f"HATA: {e}")
    sys.exit(1)