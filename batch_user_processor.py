from pyspark.sql import SparkSession
import os

# Spark Oturumu
spark = SparkSession.builder \
    .appName("UserBatchProcessor") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

path = "s3a://market-data/user_uploads/*.csv"
df = spark.read.option("header", "true").option("inferSchema", "true").csv(path)

processed_df = df.dropna().distinct()

processed_df.write.format("delta").mode("overwrite").save("s3a://market-data/gold_user_analytics")

print("Kullanıcı verisi başarıyla işlendi ve Gold katmanına yazıldı!")
spark.stop()