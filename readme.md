<div align="center"> <img src="[https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/Python-3776AB%3Fstyle%3Dfor-the-badge%26logo%3Dpython%26logoColor%3Dwhite)" /> <img src="[https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/Apache_Spark-E25A1C%3Fstyle%3Dfor-the-badge%26logo%3Dapache-spark%26logoColor%3Dwhite)" /> <img src="[https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white](https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)" /> <img src="[https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/Docker-2496ED%3Fstyle%3Dfor-the-badge%26logo%3Ddocker%26logoColor%3Dwhite)" /> <img src="[https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white](https://www.google.com/search?q=https://img.shields.io/badge/PostgreSQL-4169E1%3Fstyle%3Dfor-the-badge%26logo%3Dpostgresql%26logoColor%3Dwhite)" /> </div>

# Enterprise Real-Time Lakehouse & MLOps Platform

Bu platform, Binance WebSocket ve özel API kanalları üzerinden elde edilen gerçek zamanlı piyasa verilerini yüksek performanslı veri işleme altyapısı ile analiz eden, Delta Lake mimarisi üzerinde güvenli ve ölçeklenebilir biçimde depolayan, Apache Spark MLlib ile gelişmiş makine öğrenmesi modelleri eğiten ve dbt aracılığıyla kurumsal seviyede analitik katmanlar oluşturan uçtan uca bir veri mühendisliği ve MLOps platformudur.

Sistem mimarisi, verinin alınmasından, işlenmesine, depolanmasına, panellere aktarılmasına ve yapay zeka tabanlı tahminlerin üretilmesine kadar olan tüm süreci ortalama 5 saniye içerisinde tamamlayacak şekilde gerçek zamanlı olarak tasarlanmıştır. Bu sayede kullanıcılar, minimum gecikme ile yüksek doğruluklu analiz ve tahminlere erişebilmektedir.

Platform, yüksek maliyetli ticari kripto analiz panellerine alternatif olarak, açık kaynak felsefesiyle geliştirilmiştir. Bu sayede bireysel kullanıcılar, araştırmacılar ve şirketler, sistemi özelleştirilebilir, ölçeklenebilir ve sürdürülebilir bir şekilde kendi ihtiyaçlarına göre yapılandırabilir.

Özellikle kodlama yetkinliğine sahip kripto yatırımcıları ve veri mühendisleri, bu altyapıyı kendi stratejileri doğrultusunda geliştirerek, özel gösterge panelleri, ileri seviye analiz modülleri ve otomatik alım satım stratejileri oluşturabilir. Kurumsal tarafta ise şirketler, platformu kendi veri kaynaklarıyla entegre ederek kurum içi, yüksek performanslı ve güvenli bir analitik ekosistem inşa edebilir.

Bu mimari, gerçek zamanlı veri akışı, büyük veri işleme, gelişmiş makine öğrenmesi ve profesyonel veri modelleme süreçlerini tek çatı altında birleştirerek, modern veri platformları için güçlü ve sürdürülebilir bir referans mimari sunar.

<img width="2816" height="1536" alt="Gemini_Generated_Image_ywap46ywap46ywap" src="https://github.com/user-attachments/assets/0d3cabf3-f35d-4d77-ad85-a01477a16265" />
----------
## 📂 Proje Yapısı

```text
.
├── dags/                       # Airflow İş Akışları (DAGs)(Artık projeden kaldrıldı ama denemek ısteyenelr için silinmedi duruyor ama bir islevi yok artık)
│   ├── dbt_dag.py
│   ├── mlops_pipeline.py
│   ├── otomatik_egitim.py
│   └── spark_ml_pipeline.py
│
├── dashboard_app/              # Streamlit Kullanıcı Arayüzü
│   ├── Home.py                 # Ana Sayfa
│   ├── utils.py
│   ├── admin_modules/          # Yönetim ve Backend İşlemleri
│   └── pages/                  # Uygulama Sayfaları (Canlı Piyasa, MLOps vb.)
│
├── dbt_project/                # Veri Dönüşüm Katmanı (DBT)
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── Dockerfile
│   └── models/                 # SQL Modelleri (Staging & Marts)
│  └───target/  
├── Dokumanlar/                 # Proje Dokümantasyonu
├──25.3                         #kullancının projemle alakalı herseye ualsacagı genel yazılarım
├── batch_processor.py          # Toplu veri işleme servisi
├── Dokumanlar/                 # Proje Dokümantasyonu
├── .env                        # Çevresel Değişkenler (Şifreler - Git'e atılmaz)
├── .gitignore                  # Git
├── batch_processor.py          # Geçmiş veri (CSV) toplu işleme servisi
├── batch_user_processor.py     # Kullanıcı bazlı veri işleme
├── consumer_lake.py            # Bronze Layer Ingestion (Ham Veri Kaydedici)
├── docker-compose.yaml         # Tüm servislerin orkestrasyonu (17+ Servis)
├── Dockerfile                  # Ana Python/Spark Uygulama Image Tanımı
├── Dockerfile.connect          # Kafka Connect Özelleştirilmiş Image
├── Dockerfile.superset         # Apache Superset Özelleştirilmiş Image
├── fake_company.py             # Kurumsal Veri Simülatörü (HTTP POST)
├── ingestion_api.py            # Universal API Gateway (FastAPI)
├── ml_watcher.py               # Otonom Model Eğiticisi (Orchestrator)
├── process_silver.py           # Silver Layer Processing & AI (Spark Streaming)
├── producer.py                 # Binance WebSocket Veri Üreticisi
├── prometheus.yml              # Prometheus Metrik Konfigürasyonu
├── quality_gate.py             #  Veri Kalite Kontrolü (Data Quality Gate)
├── test_generic.py             # Endüstriyel IoT Simülasyonu
├── train_model.py              # ML Model Eğitim Motoru (Spark MLlib)
└── universal_producer.py       # Çok Amaçlı (Generic) Veri Üretici
```

##  Mimari Tasarım (Architecture)

Sistem, verinin ham halden alınarak anlamlı iş zekası raporlarına dönüşmesine kadar 5 ana katmandan oluşur:

Proje, her biri belirli bir amaca hizmet eden modüler bir yapı üzerine inşa edilmiştir. Aşağıda, sistemin omurgasını oluşturan dosyaların detaylı açıklamalarını bulabilirsiniz:

####  Veri Girişi ve API (Ingestion)

-  **`producer.py` (Real-Time Ingestion Engine):** Binance WebSocket API'sine milisaniye hassasiyetinde bağlanarak canlı piyasa verilerini yakalayan ana veri sürücüsüdür.
    
    -   **Asenkron Mesajlaşma:** Yakalanan trade verilerini Apache Kafka'nın `market_data` topic'ine asenkron olarak iletir.
        
    -   **Gelişmiş Kafka Yapılandırması:** * **Hata Toleransı:** Bağlantı kopmalarına karşı `retries=5` yapılandırması ve `acks=1` (Leader Acknowledgement) ile hız-güvenlik dengesi optimize edilmiştir.
        
        -   **Performans:** Ağ bant genişliği tasarrufu için `gzip` sıkıştırma protokolü kullanılmıştır.
            
    -   **Veri Normalizasyonu ve Zenginleştirme:** Binance'den gelen ham JSON verilerini (`s`, `p`, `q`, `T`) sistemle uyumlu `symbol`, `price`, `quantity` ve `timestamp` alanlarına haritalar (mapping).
        
    -   **Sistem İzlenebilirliği:** Verinin Binance'den çıktığı an ile sisteme girdiği anı karşılaştırmak için `event_time` (ISO format) damgası ekleyerek gecikme (latency) analizine olanak tanır.
        
    -   **Dayanıklılık (Resilience):** WebSocket bağlantısının canlı kalması için `ping_interval` kontrolü ve Kafka broker hazır olana kadar devrede kalan `time.sleep(5)` tabanlı dinamik yeniden bağlanma (reconnection) mekanizmasına sahiptir.
    
### `ingestion_api.py`
> **Önemli Not:** Bu modül sistemin ana veri akışından bağımsız olarak tasarlanmış bir **"opsiyonel genişletme katmanı"**dır. Temel amacı Binance dışındaki özel şirketlerin veya harici veri kaynaklarının kendi verilerini sisteme dahil edebilmesi için standart bir giriş kapısı sunmaktır.

-   **`ingestion_api.py` (Universal API Gateway):** FastAPI tabanlı asenkron bir uç nokta (endpoint) sunarak, dış kaynaklardan gelen özel finansal verileri Kafka ekosistemine dahil eden köprü modülüdür.
    
    -   **Esnek Veri Kabulü:** Harici şirketlerin (`symbol`, `price`, `timestamp`) formatındaki verilerini `POST` isteği ile kabul eder ve otomatik olarak `market_data` akışına enjekte eder.
        
    -   **Veri Doğrulama ve Ön İşleme:**
        
        -   Gelen isteklerde zorunlu alan kontrolü yaparak hatalı veri girişini (Bad Request) uygulama seviyesinde engeller.
            
        -   Eksik `quantity` verisi içeren isteklere otomatik olarak varsayılan değerler atayarak veri hattının sürekliliğini korur.
            
    -   **Dinamik Kafka Entegrasyonu:** `get_kafka_producer` fonksiyonu ile Singleton tasarım desenine uygun şekilde tekil bir Kafka bağlantısı oluşturur ve gelen verileri kuyruğa (queue) asenkron olarak aktarır.
        
    -   **Hata Yönetimi (Exception Handling):** Kafka bağlantı kopmaları veya geçersiz veri formatları durumunda standart HTTP 500/400 hata kodları ile istemciyi bilgilendirerek güvenli bir veri iletimi sağlar.
    
-    **`fake_company.py`**: Sistemi test etmek için geliştirilmiş bir simülatördür. Kendi şirket verileriniz varmış gibi FastAPI üzerinden sisteme veri gönderir.
    

####  Veri İşleme ve Storage (Processing & Lakehouse)

 **`process_silver.py` (The Heart of Analytics):** Apache Spark Structured Streaming mimarisini kullanarak Kafka'dan gelen ham verileri "Silver" katmanına dönüştüren ve **"in-flight"** (akış anında) AI çıkarımı yapan modüldür.

-   **Hibrit Model Yükleme (Model Persistence):** `get_model_for_symbol` fonksiyonu ile MinIO (S3) üzerindeki en güncel regresyon modellerini (RandomForest, Linear, GBT, DecisionTree) dinamik olarak yükler ve bellek yönetimi için `model_cache` mekanizmasını kullanır.
    
-   **Mikro-Yığın (Micro-batch) Stratejisi:** `.trigger(processingTime='5 seconds')` yapılandırmasıyla her 5 saniyede bir tetiklenen işlem döngüsü, düşük gecikmeli veri işleme ve veritabanı senkronizasyonu sağlar.
    
-   **Gelişmiş Veri Normalizasyonu:** Farklı kaynaklardan (Binance veya API Gateway) gelebilecek heterojen JSON verilerini `coalesce` fonksiyonu ile standartlaştırarak şema bütünlüğünü (Schema Enforcement) korur.
    
-   **7-Boyutlu Öznitelik Mühendisliği (Feature Vectorization):** Makine öğrenmesi modellerinin ihtiyaç duyduğu öznitelikleri canlı akıştan türetir:
    
    -   **İstatistiksel Analiz:** 30 saniyelik pencerelerde `stddev_pop` ile anlık volatilite hesaplaması yapar.
        
    -   **Vektörleştirme:** `VectorAssembler` kullanarak volatilite, hareketli ortalamalar ve momentum gibi 7 farklı değişkeni tek bir özellik vektöründe birleştirir.
        
-   **Çok Katmanlı Depolama (Polyglot Persistence):**
    
    -   **Lakehouse:** Analitik geçmiş ve ACID garantisi için verileri Partitioned Delta Lake (S3a) formatında arşivler.
        
    -   **Operasyonel DB:** Dashboard sisteminin anlık beslenmesi için PostgreSQL üzerine `foreachBatch` yöntemiyle asenkron yazım gerçekleştirir.
        
-   **Hata Toleransı (Resilience):** `checkpointLocation` kullanımı sayesinde sistem kesintiye uğrasa bile veri kaybı yaşamadan kaldığı yerden devam edebilen bir yapı sunar.
    

----------


-   **`consumer_lake.py` (The Data Archivist):** Apache Kafka'daki ham verileri (Raw Data) yakalayan ve ACID garantisi sunan **Delta Lake Bronze** katmanına kalıcı olarak kaydeden modüldür.
    
    -   **Spark-Delta Entegrasyonu:** Spark Session üzerinden Delta Lake uzantılarını (`DeltaSparkSessionExtension`) aktif ederek, nesne depolama katmanı (MinIO) üzerinde tam veri tutarlılığı sağlar.
        
    -   **Güvenli Veri Edinimi (Reliable Streaming):**
        
        -   **`startingOffsets: earliest`**: Kafka topic'indeki tüm geçmiş verileri en baştan itibaren okuyarak veri kaybını önler ve geçmişe dönük analiz (audit) imkanı tanır.
            
        -   **`failOnDataLoss: false`**: Herhangi bir veri kaybı durumunda sistemin durmasını engelleyerek sürekliliği (fault-tolerance) sağlar.
            
    -   **Akış Optimizasyonu (Backpressure Management):** `maxOffsetsPerTrigger=1000` yapılandırması ile her mikro-yığında maksimum 1000 mesaj işleyerek yüksek trafik altında sistemin tıkanmasını (throttling) önler.
        
    -   **Yapısal Dönüşüm:** Kafka'dan binary formatta gelen verileri string'e cast ederek tanımlanmış `StructType` şemasına göre kolonlara ayırır.
        
    -   **Delta Lake Depolama Stratejisi:**
        
        -   **`partitionBy("symbol")`**: Verileri kripto paraların sembollerine göre fiziksel klasörlere (partition) ayırarak, ilerideki sorgulama performansını optimize eder.
            
        -   **Checkpointing**: `checkpointLocation` kullanımı ile yazma işlemi sırasında oluşabilecek kesintilerde Spark'ın kaldığı yerden devam etmesini sağlar.
            
    -   **Mikro-Yığın Zamanlaması:** `trigger(processingTime='10 seconds')` ile verileri 10 saniyelik aralıklarla MinIO (S3a) üzerine `append` moduyla kalıcı olarak işler.
    
-    **`dbt_project/`**: Verinin Silver'dan Gold katmanına (Analitik katman) dönüşümü için gerekli SQL modellerini içerir. Veri temizleme ve aggregation işlemleri burada döner.
    

#### MLOps ve Otomasyon (Orchestration)


**`train_model.py` (The Intelligent Backbone):** Spark MLlib ve MLflow entegrasyonu ile çalışan, Silver katmanındaki verileri kullanarak en optimize tahmin modellerini otonom olarak üreten bir model geliştirme fabrikasıdır.

-   **Zaman Serisi Tabanlı Öznitelik Mühendisliği (`create_smart_features`):** Ham fiyat verilerini finansal göstergelere dönüştürür:
    
    -   **Lag (Gecikme) Analizi:** Geçmiş fiyat hareketlerini (`lag_1`, `lag_3`) modele girdi olarak sunar.
        
    -   **Hareketli Ortalamalar:** `ma_5` ve `ma_10` ile kısa ve orta vadeli trendleri hesaplar.
        
    -   **Dinamik Göstergeler:** Fiyat ivmesini (`momentum`) ve volatilite değişimlerini otonom olarak türetir.
        
-   **Algoritma Yarışması (AutoML League):** Sistem, her eğitim döngüsünde dört farklı güçlü algoritmayı birbiriyle yarıştırır:
    
    -   **ElasticNet (Linear Regression):** Düzenlileştirilmiş doğrusal analiz.
        
    -   **DecisionTree & RandomForest:** Karar ağacı tabanlı topluluk (ensemble) öğrenmesi.
        
    -   **GBTRegressor (Gradient Boosted Trees):** Hata odaklı ardışık modelleme.
        
-   **MLOps ve Deney Takibi (MLflow):** Her eğitim oturumu MLflow üzerinde kayıt altına alınır; RMSE ve $R^2$ metrikleri, öznitelik önem sıralamaları ve model parametreleri sistematik olarak loglanır.
    
-   **Akıllı Model Seçimi ve Dağıtımı (Champion Model):**
    
    -   **RMSE Optimizasyonu:** En düşük hata payına sahip model "KAZANAN" (Champion) olarak seçilir.
        
    -   **Production Deployment:** Kazanan model, `overwrite()` yöntemiyle MinIO (S3) üzerindeki üretim yoluna otomatik olarak taşınır ve `spark-silver` servisi tarafından canlı tahminleme için anında kullanılmaya başlanır.
        
-   **Veri Ayrıştırma Stratejisi:** Veriler rastgele değil, zaman serisi mantığına uygun olarak `%80` eğitim ve `%20` test (son gelen veriler) şeklinde kronolojik olarak ayrıştırılır (`TimeSeries Split`)

 
Paylaştığın **`ml_watcher.py`** kodu, projenin **"Otonom Karar Mekanizması"**dır. Bu modül, sistemin sürekli başında durmana gerek kalmadan, verinin olgunlaştığını anlar ve model eğitim sürecini (`train_model.py`) akıllı bir şekilde tetikler.

İşte bu kodun teknik işleyişini ve projedeki stratejik önemini anlatan profesyonel açıklama metni:

----------

### ⏳ Otonom Model İzleme ve Tetikleme Sistemi (ML Watcher)

-   **`ml_watcher.py` (The Orchestration Sentry):** Delta Lake üzerindeki veri hacmini sürekli denetleyen ve sistemin "kendi kendini eğitme" (Self-training) kabiliyetini yöneten bekçi modülüdür.
    
    -   **Olay Güdümlü Eğitim (Event-Driven Training):** Sabit bir zaman çizelgesi yerine, veri odaklı bir strateji izler:
        
        -   **Avcı Modu (Initial Hunt):** Sistem ilk başladığında, Silver katmanında `MIN_ROWS_TO_START=20` eşiğine ulaşılana kadar 10 saniyede bir tarama yaparak ilk modelin en kısa sürede üretilmesini sağlar.
            
        -   **Devriye Modu (Maintenance):** İlk eğitim tamamlandıktan sonra, sistem kaynaklarını korumak amacıyla 5 dakikalık (`NORMAL_INTERVAL_SEC`) periyotlarla düzenli kontrollere geçer.
            
    -   **Doğrudan Delta Lake Entegrasyonu:** `deltalake` kütüphanesi ve `storage_options` üzerinden MinIO (S3) ile doğrudan konuşarak Spark'a ihtiyaç duymadan veri sayımı (row count) yapar; bu sayede düşük kaynak tüketimiyle izleme gerçekleştirir.
        
    -   **Alt Süreç Yönetimi (Subprocess Orchestration):** `subprocess.run` mekanizması ile `train_model.py` dosyasını bağımsız bir işlem olarak başlatır, çıktıları (stdout/stderr) yakalayarak eğitim başarısını doğrular.
        
    -   **Hata Yönetimi ve Dayanıklılık:** Henüz veri oluşmamış olması veya ağ gecikmeleri gibi istisnai durumları `try-except` blokları ile yöneterek izleme sürecinin kesintisiz devam etmesini sağlar.
    
#### 🖥️ Arayüz ve Altyapı (UI & DevOps)

-   📊 **`dashboard.py`**: **Streamlit** ile geliştirilmiş komuta merkezidir. Canlı fiyat akışını, yapay zeka tahminlerini ve sistem sağlığını görselleştirir.
    
-   🐳 **`docker-compose.yaml`**: Tüm ekosistemi (Kafka, Spark, Airflow, MinIO, Postgres vb.) birbirine bağlı ve izole bir şekilde ayağa kaldıran ana orkestrasyon dosyasıdır.Tüm ekosistemi (17+ servis) izole ve bağımlılıkları yönetilmiş şekilde ayağa kaldırır.
    
-   📦 **`Dockerfile` / `Dockerfile.spark`**: Spark ve API gibi özel servislerin çalışması için gerekli kütüphane ve bağımlılıkların (Python, Java, Delta Jar) tanımlandığı paketleme dosyalarıdır.
    
-   📑 **`requirements.txt`**: Projenin çalışması için gerekli tüm Python kütüphanelerinin (PySpark, Kafka-Python, Delta-Spark, FastAPI) listesidir.
----------
## 🛠️ Kurulum ve Çalıştırma Rehberi
### 1. Sistemi Başlatma

Docker konteynerlerini (Kafka, Spark, Airflow, Postgres, MinIO vb.) derler ve arka planda çalıştırır:
Bash
```
İlk önce .env ile dosya olusturun.
.env
```
```
docker-compose up -d --build
```
### 2. AI Modellerini Eğitme

Sistemde yeterli veri biriktikten sonra modelleri eğitmek ve MLflow'a kaydetmek için:
Bash
```
# Checkpoint silmeden eğitim başlatmak
1.  Manuel olarak:
docker exec -it spark-silver python train_model.py
2.  Otomatik olarak:
docker exec -it spark-silver python ml_watcher.py
# Checkpoint silerek eğitimi sıfırdan baslatmak
docker exec -it spark-silver rm -rf /app/checkpoints_silver_1
```

### 3. dbt Dönüşümlerini Çalıştırma
Verileri PostgreSQL Gold katmanına dönüştürmek ve analitik hazırlık yapmak için:
Bash
```
docker exec dbt_transformer dbt run
```

----------

## 📊 İzleme ve Analiz Panelleri

**Servis Port Kullanım Amacı**

**Streamlit Dashboard**:
`http://localhost:8501` Canlı Teknik Analiz & AI Tahmin Bandı.

**Metabase BI**
`http://localhost:3005/`Kurumsal SQL Raporlama & Business Intelligence.

**MLflow**
`http://localhost:5000/`Model Versiyonlama ve Performans Takibi.

**KrafDrop**
`http://localhost:9010`Bınance veri akısını izleme.

**MinIO Console**
`http://localhost:9001`S3 Lakehouse Veri Görüntüleyici.

**Grafana**
`http://localhost:3001/`Sistem Sağlığı ve Altyapı İzleme.

**CAdvisor**
`http://localhost:8090/containers/`

**API Docs**
`http://localhost:8000/docs`FastAPI Swagger Dokümantasyonu.

----------

## 👨‍💻 Geliştirici Notları (Ops & Debug)

### **Kodlarda değişiklik yaptığında tüm sistemi kapatıp açmana gerek yok.**

örnek:Konteyneri durdurmadan dashboard kodunu güncellemek için:
Bash
```
docker cp dashboard.py dashboard:/app/dashboard.py
docker restart dashboard
```
### **Köklü Değişiklik veya Kütüphane Eklediysen (Dockerfile).**
Bash
```
docker-compose up -d --build
```

### **Veri Doğrulama (SQL)**

Verilerin doğru yazıldığını PostgreSQL içinden kontrol etmek için:
Bash
```
docker exec -it postgres psql -U admin -d market_db -c "SELECT * FROM crypto_prices LIMIT 10;"
```

### **Eklenen yeni özellikler v1**
**[TR]** Proje, başlangıçta sadece Binance API'sine bağlıyken, yapılan büyük mimari güncellemelerle **Veri Bağımsız (Data Agnostic)** bir yapıya dönüştürülmüştür. Artık sistem, veri kaynağının ne olduğuna bakmaksızın (IoT, Finans, E-Ticaret, Loglar) her türlü JSON verisini dinamik olarak işleyip MinIO Data Lake'e arşivleyebilir.
### 🚀 Key Capabilities (Neler Eklendi?)

#### 1. 🧬 Generic Producer & Schema Agnostic Ingestion

Eski "Hardcoded" (sabit kodlu) yapı terk edildi. Producer ve Kafka katmanı artık verinin içeriğiyle ilgilenmez, sadece taşıyıcı görevi görür.

-   **Önceden:** Sadece `symbol`, `price` sütunlarını kabul ediyordu.
    
-   **Şimdi:** Herhangi bir JSON yapısını kabul eder. Sistem `data_type` etiketine göre veriyi otomatik tanır.
    

#### 2. ⚡ Dynamic Spark Processing (Polymorphic Handling)

Apache Spark Streaming job'ları, gelen veriyi dinamik olarak ayrıştırır (parsing).

-   Gelen veri **CRYPTO** ise -> Finansal analiz şemasına sokar.
    
-   Gelen veri **IOT** ise -> Sensör/Telemetri şemasına sokar.
    
-   Gelen veri **LOGS** ise -> Metin analizi şemasına sokar.
    

#### 3. 🗄️ Multi-Tenant Data Lake Storage (MinIO)

Veriler MinIO üzerinde karmaşık halde değil, kaynaklarına göre otomatik bölümlenmiş (partitioned) klasörlerde saklanır.

-   `s3a://lakehouse/data/source=binance/...`
    
-   `s3a://lakehouse/data/source=iot_sensors/...`
    
-   `s3a://lakehouse/data/source=stock_market/...`
### 💻 Code Example: How It Handles Different Data

Sistemin esnekliğini gösteren JSON yapıları:

JSON

```
// Gelen Veri 1: Kripto (Sistem bunu otomatik tanır)
{
  "source": "BINANCE",
  "payload": { "symbol": "BTC", "price": 45000, "vol": 120 }
}

// Gelen Veri 2: Fabrika Sensörü (Kod değiştirmeden bunu da işler)
{
  "source": "IOT_SENSOR",
  "payload": { "device_id": "XJ-9", "temp": 85.5, "vibration": "HIGH" }
}
```
###🛡️ Data Quality Gate (Veri Kalite ve Sağlık Kapısı)
Sistemin körü körüne veri işlemesini engelleyen, **Lakehouse Mimarisinin "Doktoru"** olarak görev yapan denetim katmanıdır. Silver (İşlenmiş) katmandaki verilerin finansal ve teknik tutarlılığını analiz eder.

Büyük veri projelerindeki *"Garbage In, Garbage Out"* (Çöp girerse çöp çıkar) problemini engellemek için geliştirilmiştir.

### 🔍 Denetim Mekanizması (Audit Logic)
**`quality_gate.py`** modülü, Spark motorunu kullanarak Delta Lake üzerinde şu kritik kontrolleri gerçekleştirir:

1.  **📉 Negatif Fiyat Kontrolü (Financial Integrity):**
    * Finansal piyasalarda varlık fiyatı `0` veya negatif olamaz. Bu durum veri kaynağındaki bir hatayı (bug) işaret eder.
2.  **🧩 Eksik Veri Taraması (Null Safety):**
    * Yapay zeka modellerinin beslendiği `volatility` (oynaklık) veya teknik indikatörlerin hesaplanıp hesaplanmadığını kontrol eder.
3.  **⏳ Zaman Tutarlılığı (Temporal Validity):**
    * `processed_time` veya `event_time` alanlarında bozulma olup olmadığını, gelecekten gelen (Future Date) hatalı verileri denetler.

### 📊 Raporlama ve Aksiyon
Sistem tarama sonucunda iki tür rapor üretir:
* ✅ **PASSED (Mükemmel):** Veri seti temiz, ML modelleri eğitilebilir.
* ❌ **FAILED (Hatalı):** Kritik hatalar tespit edildi, ilgili satırlar karantinaya alınmalı veya alarm üretilmeli.

**Nasıl Çalıştırılır?**
Bu denetim, **Enterprise Control Plane (Sistem Yönetimi Paneli)** üzerinden tek tıkla canlı log takibiyle çalıştırılabildiği gibi, terminal üzerinden de tetiklenebilir:

```bash
docker exec -it spark-silver python quality_gate.py
```    

## 🤝 Katkıda Bulunun (Contributing)

Bu proje bir **YBS öğrencisi** tarafından geliştirilmiş açık kaynaklı bir framework'tür. Her türlü katkıya, fikre ve PR'a açıktır.

-   **Geliştirici:** Ömer Çakan
    
-   **LinkedIn:** www.linkedin.com/in/ömer-çakan-819751261
    
-   **Destek:** Proje size yardımcı olduysa bir ⭐ bırakmayı unutmayın!
- ### 3. Katılımcılara Özel Kod Talimatı

Kendi branch'inizi açın, ama benim `main`'ime dokunmayın."

Bash
```
# 1. Önce projeyi kendi bilgisyarına indir ya da dırekt 
github üzerinden indir
git clone https://github.com/propaper12/An-Open-Source-Real-Time-Financial-Lakehouse-Project.git
# 2. Kendi adınıza veya özelliğinize göre yeni bir branch açın
git checkout -b dev/herhangi_isim
# 3. Geliştirmenizi yapın ve sadece bu branch'e pushlayın
git push origin dev/herhangi_isim
```
## 🤝 Projenin görselleri:
<img width="1530" height="654" alt="Ekran görüntüsü 2026-02-05 174921" src="https://github.com/user-attachments/assets/d5e0de38-6b3d-4caf-aff0-bcbfeb7d27c6" />
<img width="2790" height="1415" alt="Ekran görüntüsü 2026-02-05 171703" src="https://github.com/user-attachments/assets/f86b504f-9564-41b1-8b5a-86956aba1515" />
<img width="2563" height="1467" alt="Ekran görüntüsü 2026-02-05 171629" src="https://github.com/user-attachments/assets/100441f6-084d-4f43-9fef-88006e93f122" />
<img width="2560" height="1457" alt="Ekran görüntüsü 2026-02-05 171614" src="https://github.com/user-attachments/assets/e2db796b-3dcd-452e-96b8-07e9a54289c3" />
<img width="2785" height="1454" alt="Ekran görüntüsü 2026-02-05 171552" src="https://github.com/user-attachments/assets/c4658139-de33-40a2-a99d-4a7210ae44f1" />
<img width="1095" height="730" alt="Ekran görüntüsü 2026-02-05 171448" src="https://github.com/user-attachments/assets/ab8210ca-9b1c-471c-a487-fc46b80bf481" />
<img width="1081" height="1280" alt="Ekran görüntüsü 2026-02-05 171440" src="https://github.com/user-attachments/assets/1c3657d4-c6c0-404f-af50-fd1f2c28c2fc" />
<img width="2793" height="1455" alt="Ekran görüntüsü 2026-02-05 171227" src="https://github.com/user-attachments/assets/22a9d585-84bc-424f-a320-424fc3e17227" />
<img width="2772" height="1476" alt="Ekran görüntüsü 2026-02-05 170637" src="https://github.com/user-attachments/assets/6548da13-a35f-4d57-ac58-c02da3c0969e" />
