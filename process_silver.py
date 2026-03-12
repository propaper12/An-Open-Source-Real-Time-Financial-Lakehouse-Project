import time
import os
import json
import redis
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, coalesce, window, stddev_pop, avg, last, sum, to_timestamp, when
from pyspark.sql.types import StructType, StringType, DoubleType, BooleanType
from delta.tables import DeltaTable

print("\n" + "="*60)
print("🚀 V9.0 ENTERPRISE: SMART MONEY TRACKING & CVD ENGINE")
print("="*60 + "\n")

# --- ÇEVRE DEĞİŞKENLERİ VE BAĞLANTILAR ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow_server:5000")

PG_USER = os.getenv("POSTGRES_USER", "admin_lakehouse")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "SuperSecret_DB_Password_2026")
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "market_db")
PG_URL = f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}"
PG_PROPERTIES = {"user": PG_USER, "password": PG_PASS, "driver": "org.postgresql.Driver"}

# --- REDIS BAĞLANTISI ---
try:
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)
except Exception as e:
    redis_client = None

# --- SPARK SESSION KURULUMU ---
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

spark = SparkSession.builder \
    .appName("Enterprise_Silver_Pipeline") \
    .config("spark.jars", jar_conf) \
    .config("spark.driver.extraClassPath", f"{jar_dir}/*") \
    .config("spark.executor.extraClassPath", f"{jar_dir}/*") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.shuffle.partitions", "4") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# --- KAFKA OKUMA VE ŞEMA ---
schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", DoubleType()) \
    .add("quantity", DoubleType()) \
    .add("volume_usd", DoubleType()) \
    .add("is_buyer_maker", BooleanType()) \
    .add("trade_side", StringType()) \
    .add("timestamp", StringType()) \
    .add("data", StructType().add("s", StringType()).add("p", StringType()).add("q", StringType()))

df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "market_data").option("startingOffsets", "latest").option("failOnDataLoss", "false").load()

json_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_data"))

# 💡 İŞTE BURASI ALPHA (CVD) ÜRETİM MERKEZİ!
normalized_df = json_df.select(
    coalesce(col("parsed_data.symbol"), col("parsed_data.data.s")).alias("symbol"),
    coalesce(col("parsed_data.price"), col("parsed_data.data.p").cast("double")).alias("average_price"),
    col("parsed_data.volume_usd").alias("volume_usd"),
    col("parsed_data.is_buyer_maker").alias("is_buyer_maker"),
    col("parsed_data.trade_side").alias("trade_side"),
    current_timestamp().alias("timestamp")
).withColumn(
    # Eğer Trade Side = BUY ise volume pozitif, SELL ise negatiftir.
    "volume_delta", when(col("trade_side") == "BUY", col("volume_usd")).otherwise(-col("volume_usd"))
)

# Window Aggregation (Sliding Window)
windowed_df = normalized_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "30 seconds", "5 seconds"), col("symbol")) \
    .agg(
        stddev_pop("average_price").alias("volatility"),
        avg("average_price").alias("average_price"),
        sum("volume_usd").alias("volume_usd"),        
        sum("volume_delta").alias("cvd"), # 🔴 YENİ: Kümülatif Hacim Deltası Toplamı
        last("is_buyer_maker").alias("is_buyer_maker"),
        last("trade_side").alias("trade_side"),       
        last("timestamp").alias("processed_time")
    ).na.fill(0.0, subset=["volatility", "volume_usd", "cvd"])

# --- 🧠 DISTRIBUTED MLOPS: PANDAS UDF ---
# output_schema'ya cvd alanını eklemeyi unutma!
output_schema = "symbol string, average_price double, volume_usd double, is_buyer_maker boolean, trade_side string, processed_time timestamp, volatility double, predicted_price double, cvd double"

def predict_per_symbol(pdf: pd.DataFrame) -> pd.DataFrame:
    if pdf.empty: return pdf
    symbol = pdf['symbol'].iloc[0]
    
    os.environ["MLFLOW_TRACKING_URI"] = "http://mlflow_server:5000"
    os.environ["AWS_ACCESS_KEY_ID"] = "admin"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "admin12345"
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"
    
    global_cache = globals().get("spark_model_cache", {})
    if "spark_model_cache" not in globals(): globals()["spark_model_cache"] = global_cache
        
    model = global_cache.get(symbol)
    if model is None:
        try:
            import mlflow.sklearn
            model = mlflow.sklearn.load_model(f"models:/model_{symbol}/Production")
            global_cache[symbol] = model
        except Exception: model = None

    pdf['lag_1'] = pdf['average_price']
    pdf['lag_3'] = pdf['average_price']
    pdf['ma_5'] = pdf['average_price']
    pdf['ma_10'] = pdf['average_price']
    pdf['momentum'] = 0.0
    pdf['volatility_change'] = 0.0
    
    features = pdf[["volatility", "lag_1", "lag_3", "ma_5", "ma_10", "momentum", "volatility_change"]]
    pdf["predicted_price"] = model.predict(features) if model else pdf["average_price"]
        
    return pdf[["symbol", "average_price", "volume_usd", "is_buyer_maker", "trade_side", "processed_time", "volatility", "predicted_price", "cvd"]]

predictions_df = windowed_df.groupBy("symbol").applyInPandas(predict_per_symbol, schema=output_schema)

# --- 🗄️ POLYGLOT PERSISTENCE (IDEMPOTENT SINK + CACHE) ---
def write_to_sinks(batch_df, batch_id):
    if batch_df.rdd.isEmpty(): return
    batch_df.persist()
    
    try:
        delta_path = "s3a://market-data/silver_layer_delta"
        
        # 1. DELTA LAKE MERGE
        if DeltaTable.isDeltaTable(spark, delta_path):
            dt = DeltaTable.forPath(spark, delta_path)
            dt.alias("target").merge(
                batch_df.alias("source"),
                "target.symbol = source.symbol AND target.processed_time = source.processed_time"
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        else:
            batch_df.write.format("delta").mode("overwrite").partitionBy("symbol").save(delta_path)
        
        # 2. TIMESCALEDB SINK (Postgres'te cvd kolonu olması gerekir!)
        batch_df.write.jdbc(url=PG_URL, table="market_data", mode="append", properties=PG_PROPERTIES)
        
        # 3. REDIS IN-MEMORY CACHE (VIP'ler İçin Premium Veri)
        if redis_client:
            rows = batch_df.collect()
            for row in rows:
                cache_data = {
                    "price": row["average_price"],
                    "predicted_price": row["predicted_price"],
                    "trade_side": row["trade_side"],
                    "cvd": row["cvd"] # 🔴 YENİ: API'ye CVD'yi anında buradan aktarıyoruz!
                }
                redis_client.set(f"LATEST_{row['symbol']}", json.dumps(cache_data))
                
        print(f"📦 Batch {batch_id}: Veri Delta, Postgres ve Redis'e yazıldı. (CVD Dahil)")
    except Exception as e:
        print(f"❌ Veri yazma hatası: {e}")
    finally:
        batch_df.unpersist()

# --- STREAMING EXECUTION ---
query = predictions_df.writeStream \
    .foreachBatch(write_to_sinks) \
    .outputMode("update") \
    .option("checkpointLocation", "/app/checkpoints_silver_v9") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()