import time
import os
import requests
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, coalesce, window, stddev_pop, avg, last, sum
from pyspark.sql.types import StructType, StringType, DoubleType, BooleanType

# Mimariyi V6.1 sürümüne taşıyarak ML tahminleme süreçlerini Spark içerisinden çıkardım.
# Artık Spark, ağır hesaplamaları yapıp sonuçları mikroservis olarak kurguladığım API'ye iletiyor.
print("\n" + "="*50)
print("V6.1 GÜNCELLEME: PREMIUM VERİ (VOLUME & ORDER FLOW) AKTİF")
print("="*50 + "\n")

time.sleep(3)

# --- ÇEVRE DEĞİŞKENLERİ ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")

# Model-as-a-Service (MaaS) yaklaşımı gereği bağımsız çalışan API endpoint'ini tanımladım.
INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "http://inference_api:8001/predict")

# --- POSTGRESQL BAĞLANTISI ---
PG_USER = os.getenv("POSTGRES_USER", "admin_lakehouse")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "SuperSecret_DB_Password_2026")
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")

PG_URL = f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}"
PG_PROPERTIES = {"user": PG_USER, "password": PG_PASS, "driver": "org.postgresql.Driver"}

# --- JAR AYARLARI ---
jar_dir = "/opt/spark-jars"
jar_conf = ",".join([
    f"{jar_dir}/delta-core_2.12-2.4.0.jar",
    f"{jar_dir}/delta-storage-2.4.0.jar",
    f"{jar_dir}/hadoop-aws-3.3.4.jar",
    f"{jar_dir}/aws-java-sdk-bundle-1.12.500.jar",
    f"{jar_dir}/spark-sql-kafka-0-10_2.12-3.4.1.jar",
    f"{jar_dir}/spark-token-provider-kafka-0-10_2.12-3.4.1.jar",
    f"{jar_dir}/kafka-clients-3.4.0.jar",
    f"{jar_dir}/commons-pool2-2.11.1.jar",
    f"{jar_dir}/postgresql-42.6.0.jar"
])

# --- SPARK SESSION ---
spark = SparkSession.builder \
    .appName("SilverLayer_Microservice") \
    .config("spark.jars", jar_conf) \
    .config("spark.driver.extraClassPath", f"{jar_dir}/*") \
    .config("spark.executor.extraClassPath", f"{jar_dir}/*") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.shuffle.partitions", "2") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
# 💡 NOT: Binance WebSocket üzerinden ihtiyaca göre şu ek alanlar da çekilebilir:
#    - 'E' (Event Time): Verinin oluşma anı (Milisaniye)
#    - 't' (Trade ID): İşlemin benzersiz kimliği
#    - 'b' (Buyer Order ID) & 'a' (Seller Order ID)
#    - 'T' (Trade Time): İşlemin gerçekleşme zamanı
schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", DoubleType()) \
    .add("quantity", DoubleType()) \
    .add("volume_usd", DoubleType()) \
    .add("is_buyer_maker", BooleanType()) \
    .add("trade_side", StringType()) \
    .add("timestamp", StringType()) \
    .add("source", StringType()) \
    .add("data", StructType()
         .add("s", StringType())    # Symbol
         .add("p", StringType())    # Price string
         .add("q", StringType()))   # Quantity string

print("Kafka üzerinden veri akışı dinleniyor...")
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "market_data") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

json_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_data"))

# Farklı veri kaynaklarından gelen şemaları normalize ederken YENİ kolonları da alıyoruz
normalized_df = json_df.select(
    coalesce(col("parsed_data.symbol"), col("parsed_data.data.s")).alias("symbol"),
    coalesce(col("parsed_data.price"), col("parsed_data.data.p").cast("double")).alias("average_price"),
    col("parsed_data.volume_usd").alias("volume_usd"),
    col("parsed_data.is_buyer_maker").alias("is_buyer_maker"),  # EKLENDİ
    col("parsed_data.trade_side").alias("trade_side"),
    current_timestamp().alias("timestamp")
)

# Window Aggregation: Premium Verileri de hesaplıyoruz
windowed_df = normalized_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "30 seconds", "5 seconds"), col("symbol")) \
    .agg(
        stddev_pop("average_price").alias("volatility"),
        avg("average_price").alias("average_price"),
        sum("volume_usd").alias("volume_usd"),        
        last("is_buyer_maker").alias("is_buyer_maker"), # EKLENDİ
        last("trade_side").alias("trade_side"),       
        current_timestamp().alias("processed_time")
    ).na.fill(0, subset=["volatility", "volume_usd"])

def process_batch_with_ai(batch_df, batch_id):
    """
    Spark artık verileri satır satır değil, tek bir kargo paketi (JSON Array) 
    halinde Inference API'ye gönderiyor. Network I/O darboğazı çözüldü!
    """
    if batch_df.rdd.isEmpty(): return
    
    safe_batch_df = batch_df.withColumn("processed_time", col("processed_time").cast("string"))
    pdf = safe_batch_df.toPandas()
    
    # 1. API'ye gönderilecek "Kargo Paketini" (Payload) hazırlıyoruz
    payload_data = []
    for index, row in pdf.iterrows():
        current_price = float(row['average_price'])
        volatility = float(row['volatility']) if pd.notnull(row['volatility']) else 0.0
        
        payload_data.append({
            "symbol": row['symbol'],
            "volatility": volatility,
            "lag_1": current_price, 
            "lag_3": current_price, 
            "ma_5": current_price,  
            "ma_10": current_price, 
            "momentum": 0.0,
            "volatility_change": 0.0
        })
        
    batch_payload = {"data": payload_data}
    
    pdf['predicted_price'] = pdf['average_price']
    
    # 2. TEK BİR HTTP İSTEĞİ (Batch Inference)
    BATCH_API_URL = INFERENCE_API_URL.replace("/predict", "/predict_batch") 
    
    try:
        resp = requests.post(BATCH_API_URL, json=batch_payload, timeout=3)
        if resp.status_code == 200:
            predictions = resp.json().get("predictions", [])
            pred_dict = {p['symbol']: p['predicted_price'] for p in predictions}
            pdf['predicted_price'] = pdf['symbol'].map(pred_dict).fillna(pdf['average_price'])
            print(f"Batch {batch_id}: {len(pdf)} kayıt için toplu tahmin başarıyla alındı.")
        else:
            print(f"API Hatası (Status {resp.status_code}): Fallback fiyatlar kullanılıyor.")
    except Exception as e:
        print(f"API Bağlantı Hatası: {e}. Fallback fiyatlar kullanılıyor.")

    # 3. Sonuçları Spark DataFrame'e geri çevir ve veritabanlarına yaz
    from pyspark.sql.functions import to_timestamp
    
    # YENİ VERİLERİ (volume_usd, trade_side) SİSTEME DAHİL EDİYORUZ
    pdf_final = pdf[["average_price", "predicted_price", "processed_time", "symbol", "volatility", "volume_usd", "is_buyer_maker", "trade_side"]]
    
    res_df = spark.createDataFrame(pdf_final)
    res_df = res_df.withColumn("processed_time", to_timestamp(col("processed_time")))
    
    # MinIO (Delta Lake) Kaydı
    res_df.write.format("delta") \
          .mode("append") \
          .option("mergeSchema", "true") \
          .partitionBy("symbol") \
          .save("s3a://market-data/silver_layer_delta")
    
    # PostgreSQL (TimescaleDB) Kaydı (YENİ ALANLAR EKLENDİ)
    try:
        pg_df = res_df.select("symbol", "volatility", "average_price", "processed_time", "predicted_price", "volume_usd", "is_buyer_maker", "trade_side")
        pg_df.write.jdbc(url=PG_URL, table="market_data", mode="append", properties=PG_PROPERTIES)
    except Exception as e:
        print(f"Veritabanı yazma hatası: {e}")
        
# Stream işlemini başlatıyoruz
query = windowed_df.writeStream \
    .foreachBatch(process_batch_with_ai) \
    .outputMode("update") \
    .option("checkpointLocation", "/app/checkpoints_silver_v6") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()