# 🛸 RadarPro: Deployment Mimarisi & Docker Servis Haritası

RadarPro sistemi, mikroservis mimarisi üzerine kurulu, Docker tabanlı ve saniyelik veri işleme kapasitesine sahip bir "Real-Time Intelligence" platformudur. Bu döküman, sistemdeki tüm teknolojilerin (PostgreSQL, MLflow, FastAPI, Spark, Kafka, Redis vb.) nasıl bir araya geldiğini ve hangi portlarda çalıştığını detaylandırır.

## 🛳️ Docker Servis Haritası & Port Bağlantıları

Aşağıdaki tablo, sistemdeki tüm konteynerları ve görevlerini listeler:

| Servis Adı | Teknoloji | Port(lar) | Görev / Responsibility |
| :--- | :--- | :--- | :--- |
| **api_gateway** | **FastAPI** | `8000` | Veri alımı (Ingestion) ve kullanıcı yetkilendirme. |
| **inference_api** | **FastAPI** | `8001` | ML model tahminlerini servis eden uç nokta. |
| **dashboard** | **Streamlit** | `8501` | Kullanıcı arayüzü ve gerçek zamanlı grafikler. |
| **postgres** | **TimescaleDB** | `5432` | Zaman serisi veri tabanı ve kullanıcı kayıtları. |
| **mlflow_server** | **MLflow** | `5000` | Model takibi, versiyonlama ve kayıt (Registry). |
| **redis_cache** | **Redis** | `6379` | <10ms gecikmeli arbitraj ve sinyal önbelleği. |
| **minio** | **MinIO (S3)** | `9000/9001` | Parquet veri gölü (Data Lake) ve model deposu. |
| **kafka** | **Apache Kafka** | `9092` | Canlı veri akışı ve mesaj kuyruğu. |
| **spark-silver** | **Apache Spark** | *Internal* | Anlık veri temizleme ve fiyat farkı hesaplama. |
| **db_admin** | **Adminer** | `8080` | Veritabanı yönetim arayüzü. |
| **kafdrop** | **Kafka UI** | `9010` | Kafka topic ve mesaj izleme ekranı. |

---

## 🏗️ RadarPro Servis Bağlantı Şeması

Bu şema, servislerin birbiriyle nasıl konuştuğunu ve veri akış yönünü gösterir:

```mermaid
graph LR
    %% Giriş
    User((Kullanıcı)) -->|Port 8501| DASH[Dashboard]
    User -->|Port 8000| API_GW[FastAPI Gateway]
    
    %% Veri Akışı
    API_GW -->|Port 9092| KAFKA[(Kafka)]
    KAFKA --> SPARK[[Spark Streaming]]
    
    %% Depolama & İşleme
    SPARK -->|Port 5432| PG[(PostgreSQL)]
    SPARK -->|Port 6379| REDIS[(Redis Cache)]
    SPARK -->|Port 9000| MINIO[(MinIO Lake)]
    
    %% ML Katmanı
    ML_TR[ML Trainer] -->|Port 5000| MLFLOW[MLflow Server]
    MLFLOW -->|Artifacts| MINIO
    
    %% Çıkış
    INF_API[Inference FastAPI] -->|Port 8001| User
    INF_API -->|Load Model| MLFLOW
    DASH -->|Query| PG
    DASH -->|Query| REDIS
```

---

### 🎨 Görsel Servis Haritası (RadarPro View)

Sistemin "Professional Deployment" görünümü aşağıdaki gibidir:

![RadarPro Deployment Map](file:///C:/Users/omerc/.gemini/antigravity/brain/4f82bf7b-a094-4ed6-8497-c9cf91c00029/radarpro_deployment_map_1775591928211.png)

---

### 💡 Mimari Notlar:
- **FastAPI Gücü**: Ingestion ve Inference için ayrı FastAPI servisleri kullanılarak, yoğun yük anında sistemin ölçeklenebilirliği (horizontal scaling) sağlanmıştır.
- **TimescaleDB & PostgreSQL**: Standart PostgreSQL üzerine TimescaleDB eklentisi kurularak saniyelik milyonlarca mum grafiği verisinin ultra hızlı sorgulanması sağlanmıştır.
- **MLflow**: Modellerin başarısını (Accuracy, Loss) takip etmek ve en iyi modeli canlıya almak için kullanılır.

> [!NOTE]
> `docker-compose ps` komutu ile tüm bu servislerin anlık durumunu terminal üzerinden izleyebilirsiniz.
