import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, stddev_pop, avg, current_timestamp, lit
from pyspark.ml.regression import LinearRegressionModel, RandomForestRegressionModel, GBTRegressionModel, \
    DecisionTreeRegressionModel
from pyspark.ml.feature import VectorAssembler
from functools import reduce
from pyspark.sql import DataFrame

print("Silver (Multi-Tenant Inference) Başlatılıyor...")
time.sleep(10)

spark = SparkSession.builder \
    .appName("CryptoSilverLayer") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.500,"
            "io.delta:delta-core_2.12:2.4.0,"
            "org.postgresql:postgresql:42.6.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "admin12345") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

BASE_MODEL_PATH = "s3a://market-data/models/"

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
            print(f" {symbol} Modeli Yüklendi ({loader.__name__})")
            break
        except:
            continue

    if model:
        model_cache[symbol] = model
        return model
    else:
        return None


raw_df = spark.readStream \
    .format("delta") \
    .load("s3a://market-data/raw_layer_delta")

clean_df = raw_df.select(col("symbol"), col("price").cast("double"), col("timestamp").cast("timestamp"))

windowed_df = clean_df \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "1 minute", "30 seconds"), col("symbol")) \
    .agg(
    stddev_pop("price").alias("volatility"),
    avg("price").alias("average_price"),
    current_timestamp().alias("processed_time")
)


def process_batch(batch_df, batch_id):
    if batch_df.count() == 0: return

    symbols = [row.symbol for row in batch_df.select("symbol").distinct().collect() if row.symbol]

    final_dfs = []

    for sym in symbols:
        sym_df = batch_df.filter(col("symbol") == sym).na.fill(0, subset=["volatility"])

        model = get_model_for_symbol(sym)

        res_df = sym_df
        if model:
            try:
                assembler = VectorAssembler(inputCols=["volatility"], outputCol="features")
                vec_df = assembler.transform(sym_df)
                predictions = model.transform(vec_df)
                res_df = predictions.select("symbol", "volatility", "average_price", "processed_time",
                                            col("prediction").alias("predicted_price"))
            except:
                res_df = sym_df.withColumn("predicted_price", lit(0.0))
        else:
            res_df = sym_df.withColumn("predicted_price", lit(0.0))

        final_dfs.append(res_df)

    if final_dfs:
        full_result = reduce(DataFrame.union, final_dfs)

        full_result.write \
            .format("delta") \
            .mode("append") \
            .save("s3a://market-data/silver_layer_delta")

        try:
            pg_df = full_result.select(
                col("symbol"),
                col("volatility"),
                col("average_price"),
                col("processed_time"), 
                col("predicted_price"))
            pg_df.write.jdbc(url=PG_URL, table="crypto_prices", mode="append", properties=PG_PROPERTIES)
            print(f" Batch {batch_id}: {symbols} için veriler PostgreSQL'e yazıldı.")
        except Exception as e:
            print(f" PostgreSQL Yazma Hatası: {e}")


query = windowed_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("update") \
    .option("checkpointLocation", "s3a://market-data/checkpoints_silver_multi_v2") \
    .trigger(processingTime='60 seconds') \
    .start()

query.awaitTermination()