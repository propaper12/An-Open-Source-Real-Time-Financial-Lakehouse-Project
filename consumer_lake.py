import time
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

print("[CONSUMER] Spark Delta Lake Modunda Başlatılıyor (v2.0)...")
time.sleep(20)

spark = SparkSession.builder \
    .appName("CryptoMarketLakehouse") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.500,"
            "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "admin12345") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.databricks.delta.optimizeWrite.enabled", "true") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")


schema = StructType([
    StructField("symbol", StringType()),
    StructField("price", DoubleType()),
    StructField("quantity", DoubleType()),
    StructField("timestamp", StringType())
])

print(f"Kafka Bağlantısı Başlatılıyor: {KAFKA_BOOTSTRAP_SERVERS}")

try:
    streamingDf  = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "market_data") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    value_df = streamingDf .select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    print("Delta Lake Yazma İşlemi Başlatılıyor...")
    print("NOT: Dosya sistemi sağlığı için yazma işlemi her 60 saniyede bir yapılacaktır.")

    query = value_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("path", "s3a://market-data/raw_layer_delta") \
        .option("checkpointLocation", "s3a://market-data/checkpoints_delta") \
        .trigger(processingTime='60 seconds') \
        .start()

    query.awaitTermination()

except Exception as e:
    print(f"KRİTİK HATA: {e}")
    sys.exit(1)