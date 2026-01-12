import os
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import (LinearRegression, DecisionTreeRegressor,
                                   RandomForestRegressor, GBTRegressor)
from pyspark.sql.functions import col
from pyspark.ml.evaluation import RegressionEvaluator

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MLFLOW_TRACKING_URI = "http://mlflow:5000"
DATA_PATH = "s3a://market-data/silver_layer_delta"

os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT
os.environ["AWS_ACCESS_KEY_ID"] = "admin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "admin12345"

print("🚀 MLOps Pipeline Başlatılıyor (MLflow Entegreli)...")

# MLflow Ayarları
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("Crypto_Price_Prediction_v1")

# Spark Session
spark = SparkSession.builder \
    .appName("AutoML_MLFlow") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.500,"
            "io.delta:delta-core_2.12:2.4.0,"
            "org.mlflow:mlflow-spark:1.27.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "admin12345") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

try:
    print(f"📥 Veri Okunuyor: {DATA_PATH}")
    full_df = spark.read.format("delta").load(DATA_PATH)
    
    # Hangi semboller var?
    unique_symbols = [row.symbol for row in full_df.select("symbol").distinct().collect() if row.symbol]

    for symbol in unique_symbols:
        print(f"\n🧠 {symbol} Modeli Eğitiliyor...")
        
        # Veri Hazırlığı
        clean_data = full_df.filter(col("symbol") == symbol) \
            .select("average_price", "volatility") \
            .filter((col("average_price") > 0)) \
            .dropna()

        if clean_data.count() < 10:
            print(f"Yetersiz veri: {symbol}")
            continue

        assembler = VectorAssembler(inputCols=["volatility"], outputCol="features")
        dataset = assembler.transform(clean_data).select("features", col("average_price").alias("label"))
        train_data, test_data = dataset.randomSplit([0.8, 0.2], seed=42)

        models_to_train = [
            (LinearRegression(featuresCol="features", labelCol="label", maxIter=50), "LinearRegression"),
            (RandomForestRegressor(featuresCol="features", labelCol="label", numTrees=20), "RandomForest"),
            (GBTRegressor(featuresCol="features", labelCol="label", maxIter=10), "GBT_Booster")
        ]

        for algo, model_name in models_to_train:
            with mlflow.start_run(run_name=f"{symbol}_{model_name}"):
                
                mlflow.log_param("symbol", symbol)
                mlflow.log_param("algorithm", model_name)
                
                model = algo.fit(train_data)
                predictions = model.transform(test_data)
                
                evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")
                rmse = evaluator.evaluate(predictions)
                r2 = evaluator.setMetricName("r2").evaluate(predictions)
                
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("r2", r2)
                
                print(f"  --> {model_name} | RMSE: {rmse:.4f} | R2: {r2:.4f}")

                mlflow.spark.log_model(model, "model") 

                model_save_path = f"s3a://market-data/models/{symbol}_model"
                try:
                    model.write().overwrite().save(model_save_path)
                    print(f"✅ Model Silver için kaydedildi: {model_save_path}")
                except Exception as save_err:
                    print(f"⚠️ Model S3'e kaydedilemedi: {save_err}")

                # Eğer model çok iyiyse Production için etiketle (Basit bir kural)
                if r2 > 0.8:
                    mlflow.set_tag("readiness", "production")

except Exception as e:
    print(f" HATA: {e}")

spark.stop()