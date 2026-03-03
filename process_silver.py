import time
import os
import requests
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, coalesce, window, stddev_pop, avg, last
from pyspark.sql.types import StructType, StringType, DoubleType

# Mimariyi V6.1 sürümüne taşıyarak ML tahminleme süreçlerini Spark içerisinden çıkardım.
# Artık Spark, ağır hesaplamaları yapıp sonuçları mikroservis olarak kurguladığım API'ye iletiyor.
print("\n" + "="*50)
print("V6.1 GÜNCELLEME: MICROSERVICE INFERENCE (API) AKTİF")
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
# Sistem bağımlılıklarını (Delta, AWS S3A, Kafka, Postgres) yönetmek için gerekli kütüphaneleri optimize ettim.
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
# Lakehouse mimarisini desteklemek için S3A ve Delta Lake konfigürasyonlarını yapılandırdım.
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

# Veri girişi için esnek bir şema yapısı kurguladım.
schema = StructType().add("symbol", StringType()).add("price", DoubleType()).add("quantity", DoubleType()).add("timestamp", StringType()).add("source", StringType()) \
    .add("data", StructType().add("s", StringType()).add("p", StringType()).add("q", StringType()))

print("Kafka üzerinden veri akışı dinleniyor...")
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "market_data") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

json_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_data"))

# Farklı veri kaynaklarından (Binance veya Özel API) gelen şemaları normalize ederek tek bir yapıya indirdim.
normalized_df = json_df.select(
    coalesce(col("parsed_data.symbol"), col("parsed_data.data.s")).alias("symbol"),
    coalesce(col("parsed_data.price"), col("parsed_data.data.p").cast("double")).alias("average_price"),
    current_timestamp().alias("timestamp")
)

# Window Aggregation: Veriyi 30 saniyelik pencerelerde işleyerek volatilite ve ortalama fiyat hesaplıyorum.
# Watermark kullanarak geç gelen verilerin (late data) sistemi bozmasını engelledim.
windowed_df = normalized_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "30 seconds", "5 seconds"), col("symbol")) \
    .agg(
        stddev_pop("average_price").alias("volatility"),
        avg("average_price").alias("average_price"),
        current_timestamp().alias("processed_time")
    ).na.fill(0, subset=["volatility"])

def process_batch_with_ai(batch_df, batch_id):
    """
    V6.1 GÜNCELLEMESİ: BATCH INFERENCE (Toplu Çıkarım)
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
    
    # Varsayılan tahminleri mevcut fiyat olarak ayarla (Fallback mekanizması)
    pdf['predicted_price'] = pdf['average_price']
    
    # 2. TEK BİR HTTP İSTEĞİ (100 satır bile olsa sadece 1 kere ağa çıkılır)
    BATCH_API_URL = INFERENCE_API_URL.replace("/predict", "/predict_batch") 
    
    try:
        resp = requests.post(BATCH_API_URL, json=batch_payload, timeout=3)
        if resp.status_code == 200:
            # API'den gelen toplu cevapları al
            predictions = resp.json().get("predictions", [])
            
            # Gelen tahminleri sembollere göre bir sözlüğe (dictionary) çevir
            pred_dict = {p['symbol']: p['predicted_price'] for p in predictions}
            
            # Pandas'ın vektörel gücüyle tahminleri Dataframe'e hızlıca eşleştir (map)
            pdf['predicted_price'] = pdf['symbol'].map(pred_dict).fillna(pdf['average_price'])
            print(f"Batch {batch_id}: {len(pdf)} kayıt için toplu tahmin başarıyla alındı.")
        else:
            print(f"API Hatası (Status {resp.status_code}): Fallback fiyatlar kullanılıyor.")
    except Exception as e:
        print(f"API Bağlantı Hatası: {e}. Fallback fiyatlar kullanılıyor.")

    # 3. Sonuçları Spark DataFrame'e geri çevir ve veritabanlarına yaz
    from pyspark.sql.functions import to_timestamp
    
    # ŞEMA UYUŞMAZLIĞINI (SCHEMA MISMATCH) ÖNLEMEK İÇİN YALNIZCA HEDEFLENEN SÜTUNLARI ALIYORUZ
    pdf_final = pdf[["average_price", "predicted_price", "processed_time", "symbol", "volatility"]]
    
    res_df = spark.createDataFrame(pdf_final)
    res_df = res_df.withColumn("processed_time", to_timestamp(col("processed_time")))
    
    # MinIO (Delta Lake) Kaydı - mergeSchema="true" eklenerek şema uyumsuzluğu riski sıfırlandı
    res_df.write.format("delta") \
          .mode("append") \
          .option("mergeSchema", "true") \
          .partitionBy("symbol") \
          .save("s3a://market-data/silver_layer_delta")
    
    # PostgreSQL (TimescaleDB) Kaydı
    try:
        pg_df = res_df.select("symbol", "volatility", "average_price", "processed_time", "predicted_price")
        pg_df.write.jdbc(url=PG_URL, table="market_data", mode="append", properties=PG_PROPERTIES)
    except Exception as e:
        print(f"Veritabanı yazma hatası: {e}")
        
# Stream işlemini 5 saniyelik mikro-batch pencereleriyle başlatıyorum.
# Checkpoint kullanarak olası çökme durumlarında veri kaybı olmadan kaldığı yerden devam etmesini sağladım.
query = windowed_df.writeStream \
    .foreachBatch(process_batch_with_ai) \
    .outputMode("update") \
    .option("checkpointLocation", "/app/checkpoints_silver_v6") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()