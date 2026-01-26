import os
<<<<<<< HEAD
import gc
import sys
import mlflow
import mlflow.spark
import numpy as np
from pyspark.sql import SparkSession, Window
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.regression import (LinearRegression, DecisionTreeRegressor,
                                   RandomForestRegressor, GBTRegressor)
from pyspark.sql.functions import col, lag, avg, row_number, when, isnan, count, lit
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline
=======
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import (LinearRegression, DecisionTreeRegressor,
                                   RandomForestRegressor, GBTRegressor)
from pyspark.sql.functions import col
from pyspark.ml.evaluation import RegressionEvaluator
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MLFLOW_TRACKING_URI = "http://mlflow:5000"
DATA_PATH = "s3a://market-data/silver_layer_delta"
<<<<<<< HEAD
MODELS_PATH = "s3a://market-data/models"
=======
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c

os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT
os.environ["AWS_ACCESS_KEY_ID"] = "admin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "admin12345"

<<<<<<< HEAD
print(" Enterprise AutoML Engine Başlatılıyor (Feature Engineering + TimeSeries Split)...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("RealTime_AutoML_League")

spark = SparkSession.builder \
    .appName("AutoML_Pro_Engine") \
=======
print("🚀 MLOps Pipeline Başlatılıyor (MLflow Entegreli)...")

# MLflow Ayarları
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("Crypto_Price_Prediction_v1")

# Spark Session
spark = SparkSession.builder \
    .appName("AutoML_MLFlow") \
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c
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
<<<<<<< HEAD
    .config("spark.sql.shuffle.partitions", "5") \
=======
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

<<<<<<< HEAD
def create_smart_features(df):
    """
    Ham veriden teknik analiz göstergeleri türetir.
    Sadece 'fiyat' değil, 'fiyatın hızı' ve 'yönü'nü de modele öğretir.
    """
    w = Window.partitionBy("symbol").orderBy("processed_time")
    
    df = df.withColumn("lag_1", lag("average_price", 1).over(w)) \
           .withColumn("lag_3", lag("average_price", 3).over(w))
    
    df = df.withColumn("ma_5", avg("average_price").over(w.rowsBetween(-5, 0))) \
           .withColumn("ma_10", avg("average_price").over(w.rowsBetween(-10, 0)))
    
    df = df.withColumn("momentum", col("average_price") - col("lag_3"))
    
    df = df.withColumn("volatility_change", col("volatility") - lag("volatility", 1).over(w))

    df = df.dropna()
    return df

def get_candidate_models():
    return [
        (LinearRegression(featuresCol="features", labelCol="label", maxIter=20, regParam=0.1, elasticNetParam=0.8), "ElasticNet_Reg"),
        (DecisionTreeRegressor(featuresCol="features", labelCol="label", maxDepth=8), "DecisionTree_Mid"),
        (RandomForestRegressor(featuresCol="features", labelCol="label", numTrees=20, maxDepth=10), "RandomForest_Pro"),
        (GBTRegressor(featuresCol="features", labelCol="label", maxIter=15, maxDepth=5), "GradientBoosted_X")
    ]

try:
    print(f" Veri Havuzu Taranıyor: {DATA_PATH}")
    try:
        base_df = spark.read.format("delta").load(DATA_PATH)
    except:
        base_df = spark.read.format("parquet").load(DATA_PATH)

  
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    
    target_symbols = []
    
    if target_arg != "ALL" and target_arg != "None":
        print(f"🎯 Hedef Odaklı Eğitim Modu: Sadece {target_arg} için çalışılacak.")
        count = base_df.filter(col("symbol") == target_arg).count()
        if count > 10:
            target_symbols = [target_arg]
        else:
            print(f" Uyarı: {target_arg} için yeterli veri yok ({count} satır).")
    else:
        print(" Genel Tarama Modu: Yeterli verisi olan tüm semboller taranıyor.")
        symbol_counts = base_df.groupBy("symbol").count().filter("count > 20").collect()
        target_symbols = [row.symbol for row in symbol_counts]

    if not target_symbols:
        print(" İşlenecek uygun sembol bulunamadı. Veri akışını bekleyin.")
        spark.stop()
        sys.exit(0)

    for symbol in target_symbols:
        print(f"\n⚡ ANALİZ BAŞLIYOR: {symbol}")
        
        raw_df = base_df.filter(col("symbol") == symbol)
        feature_df = create_smart_features(raw_df)
        
        input_cols = ["volatility", "lag_1", "lag_3", "ma_5", "ma_10", "momentum", "volatility_change"]
        
        assembler = VectorAssembler(inputCols=input_cols, outputCol="features_raw")
        scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)
        
        pipeline_prep = Pipeline(stages=[assembler, scaler])
        model_prep = pipeline_prep.fit(feature_df)
        final_data = model_prep.transform(feature_df).select("features", col("average_price").alias("label"), "processed_time")

        total_rows = final_data.count()
        split_index = int(total_rows * 0.8) 
        
        w_split = Window.orderBy("processed_time")
        final_data_ranked = final_data.withColumn("rank", row_number().over(w_split))
        
        train_data = final_data_ranked.filter(col("rank") <= split_index).drop("rank", "processed_time")
        test_data = final_data_ranked.filter(col("rank") > split_index).drop("rank", "processed_time")
        
        train_data.cache()
        test_data.cache()

        print(f"    Veri Seti: {total_rows} satır (Train: {train_data.count()} | Test: {test_data.count()})")

        best_rmse = float('inf')
        best_model = None
        best_model_name = ""
        
        candidates = get_candidate_models()

        for algo, name in candidates:
            with mlflow.start_run(run_name=f"{symbol}_{name}"):
                print(f"     Dövüşüyor: {name}...", end=" ")
                
                try:
                    model = algo.fit(train_data)
                    predictions = model.transform(test_data)
                    
                    evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")
                    rmse = evaluator.evaluate(predictions)
                    r2 = evaluator.setMetricName("r2").evaluate(predictions)
                    
                    print(f"-> Skor (RMSE): {rmse:.4f}")
                    
                    mlflow.log_param("symbol", symbol)
                    mlflow.log_param("features", str(input_cols))
                    mlflow.log_metric("rmse", rmse)
                    mlflow.log_metric("r2", r2)
                    
                    if hasattr(model, "featureImportances"):
                        importances = model.featureImportances.toArray()
                        mlflow.log_param("top_feature_idx", str(np.argmax(importances)))

                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_model = model
                        best_model_name = name
                        print(f"       YENİ LİDER!")

                except Exception as e:
                    print(f"HATA: {e}")
                
                gc.collect()

        if best_model:
            print(f"    KAZANAN: {best_model_name} (Hata: {best_rmse:.4f})")
            
            save_path = f"{MODELS_PATH}/{symbol}_model"
            
            best_model.write().overwrite().save(save_path)
            
            with mlflow.start_run(run_name=f"{symbol}_CHAMPION"):
                mlflow.set_tag("production_status", "active")
                mlflow.log_metric("final_rmse", best_rmse)
                mlflow.log_param("winner_algo", best_model_name)
                mlflow.spark.log_model(best_model, "model")
            
            print(f"   💾 Model Production ortamına taşındı: {save_path}")

        train_data.unpersist()
        test_data.unpersist()
        gc.collect()

except Exception as e:
    print(f"🚨 KRİTİK SİSTEM HATASI: {e}")
    import traceback
    traceback.print_exc()
=======
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
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c

spark.stop()