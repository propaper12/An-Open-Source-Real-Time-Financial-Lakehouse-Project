import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Ayarlar
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
SILVER_PATH = "s3a://market-data/silver_layer_delta"

print("🛡️ DATA QUALITY GATE (Offline Mod) Başlatılıyor...")

# Spark Session - Yerel JAR'ları kullanacak şekilde ayarlandı
# Bu sayede her açılışta 200MB indirme yapmaz, saniyesinde açılır.
spark = SparkSession.builder \
    .appName("Quality_Guard") \
    .config("spark.jars", 
            "/opt/spark-jars/delta-core_2.12-2.4.0.jar,"
            "/opt/spark-jars/delta-storage-2.4.0.jar,"
            "/opt/spark-jars/hadoop-aws-3.3.4.jar,"
            "/opt/spark-jars/aws-java-sdk-bundle-1.12.500.jar") \
    .config("spark.driver.extraClassPath", "/opt/spark-jars/*") \
    .config("spark.executor.extraClassPath", "/opt/spark-jars/*") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "admin12345") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

try:
    # Veriyi Oku
    print(f"📂 Veri Okunuyor: {SILVER_PATH}")
    
    # Delta tablosu henüz oluşmamışsa hata verebilir, kontrol ediyoruz
    try:
        df = spark.read.format("delta").load(SILVER_PATH)
    except Exception:
        print("⚠️ UYARI: Silver katmanında henüz veri yok veya tablo oluşmamış.")
        sys.exit(0)
    
    total_rows = df.count()
    print(f"📊 Toplam Analiz Edilen Satır: {total_rows}")

    if total_rows == 0:
        print("⚠️ Tablo boş, kontrol geçiliyor.")
        sys.exit(0)

    # --- KURAL SETİ ---
    
    # Kural 1: Fiyat 0 veya daha küçük olamaz
    bad_prices = df.filter(col("average_price") <= 0).count()
    
    # Kural 2: Volatilite hesaplanamamış (Null) olmamalı
    null_volatility = df.filter(col("volatility").isNull()).count()
    
    # Kural 3: Zaman damgası kontrolü
    null_time = df.filter(col("processed_time").isNull()).count()

    # --- RAPORLAMA ---
    print("\n" + "="*40)
    print("      KALİTE KONTROL RAPORU      ")
    print("="*40)

    success = True

    if bad_prices > 0:
        print(f"❌ [KRİTİK] Negatif/Sıfır Fiyat Hatası: {bad_prices} kayıt")
        success = False
    else:
        print("✅ Fiyat Kontrolü: BAŞARILI")

    if null_volatility > 0:
        print(f"⚠️ [UYARI] Eksik Volatilite Verisi: {null_volatility} kayıt")
    else:
        print("✅ Volatilite Kontrolü: BAŞARILI")
        
    if null_time > 0:
        print(f"❌ [KRİTİK] Zaman Damgası Hatası: {null_time} kayıt")
        success = False
    else:
        print("✅ Zaman Damgası Kontrolü: BAŞARILI")

    print("-" * 40)
    
    if success:
        print("🎉 SONUÇ: VERİ KALİTESİ MÜKEMMEL (PASSED)")
    else:
        print("🚫 SONUÇ: VERİDE HATALAR VAR (FAILED)")

except Exception as e:
    print(f"⚠️ Kritik Sistem Hatası: {e}")

spark.stop()