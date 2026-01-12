# Enterprise Real-Time Lakehouse & MLOps Platform

Bu platform; Binance WebSocket ve özel API kanallarından gelen canlı market verilerini işleyen, **Delta Lake** mimarisi üzerinde depolayan, **Spark MLlib** ile yapay zeka modelleri eğiten ve **dbt** ile profesyonel analitik katmanlar oluşturan uçtan uca bir veri mühendisliği iskeletidir.
<img width="8192" height="1912" alt="Untitled diagram-2026-01-12-172902" src="https://github.com/user-attachments/assets/e2975ffb-1d66-4144-a29a-80cd2f462182" />

----------

## 🏗️ Mimari Tasarım (Architecture)

Sistem, verinin ham halden alınarak anlamlı iş zekası raporlarına dönüşmesine kadar 5 ana katmandan oluşur:




Proje, her biri belirli bir amaca hizmet eden modüler bir yapı üzerine inşa edilmiştir. Aşağıda, sistemin omurgasını oluşturan dosyaların detaylı açıklamalarını bulabilirsiniz:

#### 📥 Veri Girişi ve API (Ingestion)

-   🚀 **`producer.py`**: Binance WebSocket API'sine bağlanarak canlı piyasa verilerini (Trade) yakalar ve **Apache Kafka**'ya "raw-trades" topic'i üzerinden asenkron olarak basır.
    
-   ⚡ **`ingestion_api.py`**: FastAPI tabanlı bir gateway'dir. Dış kurumsal kaynaklardan (örneğin Tesla) gelen verileri kabul eder ve Kafka'ya yönlendirir.
    
-   🏢 **`fake_company.py`**: Sistemi test etmek için geliştirilmiş bir simülatördür. Kendi şirket verileriniz varmış gibi FastAPI üzerinden sisteme veri gönderir.
    

#### ⚙️ Veri İşleme ve Storage (Processing & Lakehouse)

-   🌊 **`process_silver.py`**: Sistemin ana motoru (Spark Streaming). Kafka'dan veriyi okur, şema doğrulaması yapar, **Spark ML** modellerini kullanarak "In-flight" tahminleme yapar ve sonuçları **Delta Lake Silver** katmanına yazar.
    
-   🥉 **`consumer_lake.py`**: Kafka'dan gelen ham verileri hiçbir değişikliğe uğratmadan **Delta Lake Bronze** katmanına (Raw Data) yazar; veri geçmişinin korunmasını (Audit) sağlar.
    
-   🏗️ **`dbt_project/`**: Verinin Silver'dan Gold katmanına (Analitik katman) dönüşümü için gerekli SQL modellerini içerir. Veri temizleme ve aggregation işlemleri burada döner.
    

#### 🧠 MLOps ve Otomasyon (Orchestration)

-   🧪 **`train_model.py`**: Delta Lake'deki geçmiş verileri kullanarak model eğitir. **MLflow** ile entegre çalışarak her eğitimdeki metrikleri (RMSE, MAE vb.) ve model dosyalarını kayıt altına alır.
    
-   📅 **`dags/`**: **Apache Airflow** tarafından kullanılan DAG dosyalarıdır. Modellerin haftalık yeniden eğitilmesi veya dbt dönüşümlerinin periyodik çalışması burada planlanır.
    

#### 🖥️ Arayüz ve Altyapı (UI & DevOps)

-   📊 **`dashboard.py`**: **Streamlit** ile geliştirilmiş komuta merkezidir. Canlı fiyat akışını, yapay zeka tahminlerini ve sistem sağlığını görselleştirir.
    
-   🐳 **`docker-compose.yaml`**: Tüm ekosistemi (Kafka, Spark, Airflow, MinIO, Postgres vb.) birbirine bağlı ve izole bir şekilde ayağa kaldıran ana orkestrasyon dosyasıdır.
    
-   📦 **`Dockerfile` / `Dockerfile.spark`**: Spark ve API gibi özel servislerin çalışması için gerekli kütüphane ve bağımlılıkların (Python, Java, Delta Jar) tanımlandığı paketleme dosyalarıdır.
    
-   📑 **`requirements.txt`**: Projenin çalışması için gerekli tüm Python kütüphanelerinin (PySpark, Kafka-Python, Delta-Spark, FastAPI) listesidir.
----------
## 🛠️ Kurulum ve Çalıştırma Rehberi
### 1. Sistemi Başlatma

Docker konteynerlerini (Kafka, Spark, Airflow, Postgres, MinIO vb.) derler ve arka planda çalıştırır:
Bash
```
docker-compose up -d --build
```
### 2. Şirket Veri Simülasyonunu Başlatma

Özel şirket akışını tetiklemek (Tesla vb.) ve API'yi test etmek için:
Bash
```
python fake_company.py
```

### 3. AI Modellerini Eğitme

Sistemde yeterli veri biriktikten sonra modelleri eğitmek ve MLflow'a kaydetmek için:
Bash
```
docker exec spark-silver python train_model.py
```

### 4. dbt Dönüşümlerini Çalıştırma
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

**Airflow UI**
`http://localhost:8081`Pipeline Otomasyonu ve DAG Yönetimi.

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

### **Roadmap & Gelecek Planları**

-   [ ] GitHub Actions ile CI/CD Pipeline Entegrasyonu.
    
-   [ ] Great Expectations ile Data Quality Checks.
    
-   [ ] Slack/Telegram üzerinden hata bildirimleri.
    

----------

## 🤝 Katkıda Bulunun (Contributing)

Bu proje bir **YBS öğrencisi** tarafından geliştirilmiş açık kaynaklı bir framework'tür. Her türlü katkıya, fikre ve PR'a açıktır.

-   **Geliştirici:** Ömer Çakan
    
-   **LinkedIn:** [Profil Linkini Buraya Yapıştır]
    
-   **Destek:** Proje size yardımcı olduysa bir ⭐ bırakmayı unutmayın!
- ### 3. Katılımcılara Özel Kod Talimatı

Kendi branch'inizi açın, ama benim `main`'ime dokunmayın."

Bash
```
# 1. Önce projeyi yerele indir
git clone https://github.com/propaper12/An-Open-Source-Real-Time-Financial-Lakehouse-Project.git

# 2. Kendi adınıza veya özelliğinize göre yeni bir branch açın
git checkout -b dev/herhangi_isim

# 3. Geliştirmenizi yapın ve sadece bu branch'e pushlayın
git push origin dev/herhangi_isim
```
