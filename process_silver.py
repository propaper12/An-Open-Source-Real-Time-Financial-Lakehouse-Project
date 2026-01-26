import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, coalesce, lit, window, stddev_pop, avg
from pyspark.sql.types import StructType, StringType, DoubleType
from pyspark.ml.regression import LinearRegressionModel, RandomForestRegressionModel, GBTRegressionModel, DecisionTreeRegressionModel
from pyspark.ml.feature import VectorAssembler
from functools import reduce
from pyspark.sql import DataFrame
import os

print(" Universal Silver Processor  Başlatılıyor...")
time.sleep(5)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BASE_MODEL_PATH = "s3a://market-data/models/"

spark = SparkSession.builder \
    .appName("UniversalSilverProcessor") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.500,"
            "io.delta:delta-core_2.12:2.4.0,"
            "org.postgresql:postgresql:42.6.0") \
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
PG_PROPERTIES = {
    "user": "admin", 
    "password": "admin",
    "driver": "org.postgresql.Driver"
}

model_cache = {}

def get_model_for_symbol(symbol):
    if symbol in model_cache:
        return model_cache[symbol]

    path = f"{BASE_MODEL_PATH}{symbol}_model"
    model = None
    loaders = [RandomForestRegressionModel, LinearRegressionModel, GBTRegressionModel, DecisionTreeRegressionModel]

    for loader in loaders:
        try:
            model = loader.load(path)
            print(f" {symbol} için Yapay Zeka Modeli Yüklendi: {loader.__name__}")
            break
        except:
            continue

    if model:
        model_cache[symbol] = model
        return model
    else:
        return None

schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", DoubleType()) \
    .add("quantity", DoubleType()) \
    .add("timestamp", StringType()) \
    .add("source", StringType()) \
    .add("data", StructType()
         .add("s", StringType())
         .add("p", StringType())
         .add("q", StringType())
    )

print("📡 Kafka Dinleniyor (Topic: market_data)...")
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "market_data") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .load()


json_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_data"))

normalized_df = json_df.select(
    coalesce(col("parsed_data.symbol"), col("parsed_data.data.s")).alias("symbol"),
    coalesce(col("parsed_data.price"), col("parsed_data.data.p").cast("double")).alias("average_price"),
    coalesce(col("parsed_data.quantity"), col("parsed_data.data.q").cast("double")).alias("quantity"),
    coalesce(col("parsed_data.source"), lit("Legacy_Source")).alias("source_system"),
    current_timestamp().alias("timestamp")
)

windowed_df = normalized_df \
    .withWatermark("timestamp", "30 seconds") \
    .groupBy(window(col("timestamp"), "30 seconds", "15 seconds"), col("symbol")) \
    .agg(
        stddev_pop("average_price").alias("volatility"),
        avg("average_price").alias("average_price"),
        current_timestamp().alias("processed_time")
    ).na.fill(0, subset=["volatility"])

def process_batch_with_ai(batch_df, batch_id):
    if batch_df.rdd.isEmpty(): 
        return

    batch_df.persist()

    try:
        symbols = [row.symbol for row in batch_df.select("symbol").distinct().collect() if row.symbol]
        final_dfs = []

        for sym in symbols:
            sym_df = batch_df.filter(col("symbol") == sym)
            model = get_model_for_symbol(sym)
            res_df = sym_df

            if model:
                try:
                    assembler = VectorAssembler(inputCols=["volatility"], outputCol="features")
                    vec_df = assembler.transform(sym_df)
                    predictions = model.transform(vec_df)
                    res_df = predictions.select(
                        "symbol", "volatility", "average_price", "processed_time",
                        col("prediction").alias("predicted_price")
                    )
                except Exception as e:
                    print(f" Model hatası ({sym}): {e}")
                    res_df = sym_df.withColumn("predicted_price", lit(0.0))
            else:
                res_df = sym_df.withColumn("predicted_price", col("average_price"))

            final_dfs.append(res_df)

        if final_dfs:
            full_result = reduce(DataFrame.union, final_dfs)

            full_result.write \
                .format("delta") \
                .mode("append") \
                .partitionBy("symbol") \
                .save("s3a://market-data/silver_layer_delta")

            try:
                pg_df = full_result.select("symbol", "volatility", "average_price", "processed_time", "predicted_price")
                pg_df.write.jdbc(url=PG_URL, table="market_data", mode="append", properties=PG_PROPERTIES)
            except Exception as e:
                print(f" PostgreSQL Yazma Hatası: {e}")
                
    except Exception as e:
        print(f"Batch İşleme Hatası: {e}")
    finally:
        batch_df.unpersist()

print(" Universal AI Processor Devrede...")
query = windowed_df.writeStream \
    .foreachBatch(process_batch_with_ai) \
    .outputMode("update") \
    .option("checkpointLocation", "/app/checkpoints_silver_universal") \
    .trigger(processingTime='5 seconds') \
    .start()

query.awaitTermination()