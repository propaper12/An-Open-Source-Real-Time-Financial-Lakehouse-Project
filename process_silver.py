import time
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, coalesce, lit, window, stddev_pop, avg, last
from pyspark.sql.types import StructType, StringType, DoubleType
from pyspark.ml.regression import LinearRegressionModel, RandomForestRegressionModel, GBTRegressionModel, DecisionTreeRegressionModel
from pyspark.ml.feature import VectorAssembler, StandardScalerModel
from functools import reduce
from pyspark.sql import DataFrame

# --- LOGLARDA GÖRÜNMESİ İÇİN ---
print("\n" + "="*50)
print("🚀 V5.0 GÜNCELLEME: VECTOR FIX (7-DIMENSION) AKTİF")
print("="*50 + "\n")

time.sleep(5)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BASE_MODEL_PATH = "s3a://market-data/models/"

# JAR Ayarları (Aynı kalıyor)
jar_dir = "/opt/spark-jars"
jar_list = [
    f"{jar_dir}/delta-core_2.12-2.4.0.jar",
    f"{jar_dir}/delta-storage-2.4.0.jar",
    f"{jar_dir}/hadoop-aws-3.3.4.jar",
    f"{jar_dir}/aws-java-sdk-bundle-1.12.500.jar",
    f"{jar_dir}/spark-sql-kafka-0-10_2.12-3.4.1.jar",
    f"{jar_dir}/spark-token-provider-kafka-0-10_2.12-3.4.1.jar",
    f"{jar_dir}/kafka-clients-3.4.0.jar",
    f"{jar_dir}/commons-pool2-2.11.1.jar",
    f"{jar_dir}/postgresql-42.6.0.jar"
]
jar_conf = ",".join(jar_list)

spark = SparkSession.builder \
    .appName("UniversalSilverProcessor") \
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
    .config("spark.sql.shuffle.partitions", "5") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

PG_URL = "jdbc:postgresql://postgres:5432/market_db"
PG_PROPERTIES = {"user": "admin", "password": "admin", "driver": "org.postgresql.Driver"}

model_cache = {}

def get_model_for_symbol(symbol):
    if symbol in model_cache:
        return model_cache[symbol]
    
    path = f"{BASE_MODEL_PATH}{symbol}_model"
    # Tüm olası model tiplerini deniyoruz
    loaders = [RandomForestRegressionModel, LinearRegressionModel, GBTRegressionModel, DecisionTreeRegressionModel]
    
    for loader in loaders:
        try:
            model = loader.load(path)
            print(f"✅ Model Yüklendi: {symbol} -> {loader.__name__}")
            model_cache[symbol] = model
            return model
        except:
            continue
    return None

schema = StructType().add("symbol", StringType()).add("price", DoubleType()).add("quantity", DoubleType()).add("timestamp", StringType()).add("source", StringType()) \
    .add("data", StructType().add("s", StringType()).add("p", StringType()).add("q", StringType()))

print("📡 Kafka Bağlanıyor...")
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "market_data") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

json_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_data"))

normalized_df = json_df.select(
    coalesce(col("parsed_data.symbol"), col("parsed_data.data.s")).alias("symbol"),
    coalesce(col("parsed_data.price"), col("parsed_data.data.p").cast("double")).alias("average_price"),
    coalesce(col("parsed_data.quantity"), col("parsed_data.data.q").cast("double")).alias("quantity"),
    current_timestamp().alias("timestamp")
)

# Window Aggregation (Temel veriler)
windowed_df = normalized_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "30 seconds", "10 seconds"), col("symbol")) \
    .agg(
        stddev_pop("average_price").alias("volatility"),
        avg("average_price").alias("average_price"),
        last("average_price").alias("last_price"),
        current_timestamp().alias("processed_time")
    ).na.fill(0, subset=["volatility"])

def process_batch_with_ai(batch_df, batch_id):
    if batch_df.rdd.isEmpty(): return
    batch_df.persist()

    try:
        symbols = [row.symbol for row in batch_df.select("symbol").distinct().collect() if row.symbol]
        final_dfs = []

        for sym in symbols:
            sym_df = batch_df.filter(col("symbol") == sym)
            model = get_model_for_symbol(sym)
            
            # --- KRİTİK BÖLÜM: Feature Vector Hazırlığı ---
            # Model 7 özellik bekliyor: ["volatility", "lag_1", "lag_3", "ma_5", "ma_10", "momentum", "volatility_change"]
            # Streaming'de 'lag' olmadığı için mevcut fiyatı baz alarak dolduruyoruz.
            
            prep_df = sym_df \
                .withColumn("lag_1", col("average_price")) \
                .withColumn("lag_3", col("average_price")) \
                .withColumn("ma_5", col("average_price")) \
                .withColumn("ma_10", col("average_price")) \
                .withColumn("momentum", lit(0.0)) \
                .withColumn("volatility_change", lit(0.0))

            # Modelin beklediği sütun sırası
            input_cols = ["volatility", "lag_1", "lag_3", "ma_5", "ma_10", "momentum", "volatility_change"]
            
            # Vektör birleştirici
            assembler = VectorAssembler(inputCols=input_cols, outputCol="features_raw")
            
            try:
                vec_df = assembler.transform(prep_df)
                
                # Model 'features' adında bir kolon bekler.
                # Eğer modelin içinde Scaler yoksa, raw features'ı direkt features yapıyoruz.
                final_input_df = vec_df.withColumnRenamed("features_raw", "features")
                
                if model:
                    predictions = model.transform(final_input_df)
                    res_df = predictions.select(
                        "symbol", "volatility", "average_price", "processed_time",
                        col("prediction").alias("predicted_price")
                    )
                else:
                    res_df = sym_df.withColumn("predicted_price", col("average_price"))
                    
            except Exception as e:
                print(f"⚠️ Tahmin Hatası ({sym}): {e}")
                res_df = sym_df.withColumn("predicted_price", col("average_price"))

            final_dfs.append(res_df)

        if final_dfs:
            full_result = reduce(DataFrame.union, final_dfs)
            
            # Delta Lake'e yaz
            full_result.write.format("delta").mode("append").partitionBy("symbol").save("s3a://market-data/silver_layer_delta")
            
            # Postgres'e yaz (Dashboard için)
            try:
                pg_df = full_result.select("symbol", "volatility", "average_price", "processed_time", "predicted_price")
                pg_df.write.jdbc(url=PG_URL, table="market_data", mode="append", properties=PG_PROPERTIES)
                print(f"✅ Batch {batch_id} Başarıyla İşlendi.")
            except Exception as e:
                print(f"❌ DB Yazma Hatası: {e}")

    except Exception as e:
        print(f"🚨 Batch İşleme Hatası: {e}")
    finally:
        batch_df.unpersist()

query = windowed_df.writeStream \
    .foreachBatch(process_batch_with_ai) \
    .outputMode("update") \
    .option("checkpointLocation", "/app/checkpoints_silver_v5") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()