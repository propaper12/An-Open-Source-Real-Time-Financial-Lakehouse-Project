# 🚀 RadarPro: Uçtan Uca Sistem Mimarisi & Servis Bağlantı Haritası

Bu döküman, RadarPro platformunun **10+ farklı kripto borsasından** veri çekişinden başlayarak, **Makine Öğrenmesi** ve **Gerçek Zamanlı Arbitraj** çıktılarına kadar olan tüm teknolojik katmanlarını tek bir "Servis Bağlantı Haritası" üzerinde birleştirir.

---

## 📊 Entegre Sistem Mimari Şeması (Master Connection Map)

Aşağıdaki şema, verinin tüm duraklarını ve servislerin birbiriyle olan saniyelik etkileşimlerini gösterir:

```mermaid
graph TD
    %% Veri Kaynakları Layer
    subgraph "🌐 10+ Farklı Kripto Borsası (Ingestion Layer)"
        EX[Binance, Kraken, Bybit, OKX, vb.]
        API_GW[FastAPI Ingestion Gateway\nPort 8000]
    end

    %% Mesaj Kuyruğu Layer
    subgraph "⚡ Real-Time Streaming & Message Bus"
        KAFKA[(Apache Kafka\nPort 9092)]
        KAFDROP[Kafdrop UI\nPort 9010]
    end

    %% İşleme Layer
    subgraph "⚙️ Veri İşleme & Pipeline (Spark Engine)"
        SP_CONS[Spark Consumer\nDeep Lake Writing]
        SP_SILV[Spark Silver Process\nCleansing & Arbitrage Calc]
    end

    %% Depolama & Cache Layer
    subgraph "🚀 Depolama & Fast Cache (Data Hub)"
        PG[(PostgreSQL / TimescaleDB\nPort 5432)]
        REDIS((Redis Cache\nPort 6379))
        MINIO[(MinIO / S3 Storage\nPort 9000)]
    end

    %% ML & Forecasting Layer
    subgraph "🧠 AI / ML Pipeline"
        ML_TR[ML Trainer\nGradient Boosting / RNN]
        MLFLOW[MLflow Server\nPort 5000]
        INF_API[Inference FastAPI\nPort 8001]
    end

    %% Kullanıcı Arayüzü
    subgraph "📈 Dashboard & UI (Vision)"
        DASH[Streamlit Radar\nPort 8501]
    end

    %% Veri Akış Okları (Bağlantılar)
    EX -->|CCXT / Producer| KAFKA
    API_GW -->|Validasyonlu Veri| KAFKA
    KAFKA <-.->|Monitor| KAFDROP
    
    KAFKA -->|Streaming Data| SP_CONS
    KAFKA -->|Real-Time Sink| SP_SILV
    
    SP_CONS -->|Parquet Data| MINIO
    SP_SILV -->|Arbitraj Sinyalleri| REDIS
    SP_SILV -->|Zaman Serisi Market Verisi| PG
    
    MINIO -->|Eğitim Veri Seti| ML_TR
    ML_TR -->|Model / Metric Log| MLFLOW
    MLFLOW -->|Registry| MINIO
    
    MLFLOW -->|Model Load| INF_API
    INF_API -->|Canlı Tahminler| DASH
    
    PG -->|Geçmiş Veriz / Query| DASH
    REDIS -->|Live Arbitraj Radar| DASH
```

---

## 🛠️ Teknoloji Yığın Portları ve Sorumlulukları

| Katman | Teknoloji | Port | Sorumluluk |
| :--- | :--- | :--- | :--- |
| **Ingestion** | **FastAPI** | `8000` | Dış dünyadan veri kabulü ve güvenlik. |
| **Predict** | **FastAPI** | `8001` | Modellerin AI tahminlerini dışa açma. |
| **Tracking** | **MLflow** | `5000` | Modellerin "hangi sürüm daha iyi?" takibi. |
| **DB (SQL)** | **Postgres (TSDB)** | `5432` | Milyonlarca satır market verisinin ultra-hızlı sorgulanması. |
| **Cache** | **Redis** | `6379` | <10ms arbitraj sinyal radarı. |
| **Lake** | **MinIO** | `9000` | Büyük verilerin (Parquet) ve modellerin saklanması. |
| **Stream** | **Kafka** | `9092` | Sistemin atardamarı; veriyi kayıpsız taşır. |
| **UI** | **Streamlit** | `8501` | Analistin tüm sistemi yönettiği ana kontrol merkezi. |

---

### 🎨 RadarPro: Profesyonel Bakış (3D Mockup)

Aşağıdaki görsel, sistemin katmanlı ve birbirine bağlı mikroservis yapısını en üst düzeyde temsil eder:

![RadarPro Unified Architecture](file:///C:/Users/omerc/.gemini/antigravity/brain/4f82bf7b-a094-4ed6-8497-c9cf91c00029/radarpro_deployment_map_1775591928211.png)

### 💡 Mimari Güç Noktaları:
- **Hızlı Arbitraj**: Borsa verileri Kafka -> Spark -> Redis hattından geçerek milisaniyeler içinde dashboard'a uçarak arbitraj fırsatını kaçırmamanızı sağlar.
- **Güvenli API**: Ingestion API (FastAPI) ile sisteme giren her veri otomatik olarak şemaya göre valide edilir.
- **Model Versiyonlama**: MLflow sayesinde sistemde her zaman "En İyi Performans Gösteren (Champion)" model otomatik olarak aktif edilir.

---

## 🔄 Şekil 4.2: inference_api.py — Redis Pub/Sub ile Zero-Downtime Model Güncelleme Akışı

RadarPro, canlı sistemde çalışan Makine Öğrenmesi modellerini güncellemek için sunucuyu kapatıp açmaya gerek duymaz. Bu "Sıfır Kesinti" (Zero-Downtime) mekanizması, **Redis Pub/Sub** üzerinden tüm worker'lara anlık sinyal gönderilmesiyle sağlanır.

### 🔌 Model Güncelleme Mekanizması (Graph TD)

```mermaid
graph TD
    subgraph "🧠 ML Ops Pipeline"
        TRAINER[ML Trainer / Watcher]
        MLF[(MLflow Model Registry)]
    end

    subgraph "⚡ Message Bus (Sync)"
        REDIS((Redis Pub/Sub\nChannel: model_updates))
    end

    subgraph "🚀 Inference API (Multi-Worker)"
        W1[FastAPI Worker 1\nRAM Cache]
        W2[FastAPI Worker 2\nRAM Cache]
        W3[FastAPI Worker N\nRAM Cache]
    end

    %% Akış
    TRAINER -->|1. Yeni Model Kaydet| MLF
    TRAINER -->|2. Yayınla: RELOAD_MODELS| REDIS
    
    REDIS -.->|3. Anlık Sinyal Dinle| W1
    REDIS -.->|3. Anlık Sinyal Dinle| W2
    REDIS -.->|3. Anlık Sinyal Dinle| W3
    
    W1 -->|4. Cache Sil & MLflow'dan Çek| MLF
    W2 -->|4. Cache Sil & MLflow'dan Çek| MLF
    W3 -->|4. Cache Sil & MLflow'dan Çek| MLF
```

### 🛠️ Teknik İşleyiş Adımları:
1.  **Model Kaydı**: `ml_watcher.py` yeni ve daha başarılı bir model eğittiğinde bunu MLflow'a `Production` tag'i ile kaydeder.
2.  **Sinyal Yayınlama**: Kayıt işlemi biter bitmez Redis üzerindeki `model_updates` kanalına `RELOAD_MODELS` mesajı gönderilir.
3.  **Anlık Yakalama**: Arka planda çalışan `asyncio` tabanlı Redis dinleyicisi bu mesajı yakalar.
4.  **RAM Cache Temizliği**: API'nin içindeki `model_cache` global değişkeni temizlenir.
5.  **Dynamic Loading**: İlk gelen prediction isteğinde, yeni model MLflow'dan saniyeler içinde RAM'e çekilir ve tahmin işlemi kesintisiz devam eder.

---

## 🏗️ Şekil 4.3: Docker Compose — Konteyner Ağı ve Servisler Arası Bağlantı Mimarisi

RadarPro sistemi, tüm mikroservislerin güvenli ve hızlı bir şekilde haberleşebilmesi için izole bir **Docker Bridge Network** (`data-network`) kullanır. Bu ağ içerisinde servisler birbirlerine IP adresleri yerine konteyner isimleri (Service Discovery) üzerinden erişirler.

### 🔌 Ağ ve Bağlantı Şeması

```mermaid
graph TD
    subgraph "🌐 External Access (Public Ports)"
        P8501["Port 8501: UI"]
        P8000["Port 8000: Ingestion"]
        P8001["Port 8001: Inference"]
        P5432["Port 5432: DB"]
        P5000["Port 5000: MLflow"]
    end

    subgraph "🐳 Docker Internal Network (data-network)"
        direction TB
        KAFKA["kafka:9092"]
        DB["postgres:5432"]
        MINIO["minio:9000"]
        REDIS["redis:6379"]
        MLF["mlflow_server:5000"]
        
        subgraph "⚙️ Internal Workers"
            SPARK[spark-silver]
            ML_T[ml-trainer]
        end
    end

    %% Bağlantılar
    P8501 --> DASH[dashboard]
    DASH -.-> DB
    DASH -.-> REDIS
    
    SPARK --> KAFKA
    SPARK --> DB
    SPARK --> MINIO
    
    ML_T --> MINIO
    ML_T --> MLF
    
    API[api_gateway] --> KAFKA
    
    %% Volume simgesi
    KAFKA --- VOL1[("(kafka_data)")]
    DB --- VOL2[("(postgres_data)")]
    MINIO --- VOL3[("(minio_data)")]
```

### 🛠️ Kritik Ağ Özellikleri:
1.  **Service Discovery**: Kod içerisinde veritabanına bağlanırken `localhost` yerine `postgres` host adının kullanılması Docker tarafından otomatik yönetilir.
2.  **İzolasyon**: `zookeeper` gibi dış dünyaya kapalı servisler sadece iç ağdan erişilebilir, bu da sistem güvenliğini artırır.
3.  **Persistency (Hacimler)**: Konteynerlar silinse bile veriler fiziksel hacimlerde korunur.

---

## 📈 Şekil 6.1: producer.py — Binance Futures 76-Stream WebSocket Veri Toplama Mimarisi

Sistemin veri giriş (Ingestion) katmanındaki en kritik bileşenlerden biri olan `producer.py`, Binance vadeli işlemler (Futures) borsasından **76 farklı veri akışını (stream)** tek bir WebSocket bağlantısı üzerinden eşzamanlı olarak toplar.

### 🔬 Teknik Detaylar:
- **Bağlantı Türü**: Binance Futures Multi-Stream WebSocket (`wss://fstream.binance.com/stream`)
- **Stream Yapısı**: 
    - `25 Coin x 3 Stream` (aggTrade, depth20, markPrice) = **75 Stream**
    - `!forceOrder@arr` (Küresel Likidasyon Akışı) = **1 Stream**
    - **Toplam**: **76 Aktif Stream**

```mermaid
graph TD
    subgraph "🟠 Binance Futures WebSocket Engine"
        WS[wss://fstream.binance.com]
        
        subgraph "📡 76 Aktif Stream Feed"
            LIQ["!forceOrder@arr - Liquidation"]
            TRADE["25x Aggregated Trades"]
            DEPTH["25x OrderBook Depth20 @100ms"]
            PRICE["25x Mark Price / Funding Rate"]
        end
    end

    subgraph "🐍 producer.py Logic (Python)"
        PROC{Process Logic}
        STATE[In-Memory Market State]
        MAP[JSON Parser & Mapper]
    end

    subgraph "⚡ Output"
        KAFKA_PROD[Kafka Producer - GZIP Compression]
        TOPIC[(Topic: market_data)]
    end

    %% Akış
    WS -->|Raw JSON| PROC
    PROC -->|Update| STATE
    STATE -->|Merge Data| MAP
    MAP -->|Serialized JSON| KAFKA_PROD
    KAFKA_PROD --> TOPIC
```

### 🎯 Veri Toplama Stratejisi:
1.  **Likidasyon Takibi**: `!forceOrder@arr` ile marketteki tüm büyük tasfiyeler anlık yakalanır.
2.  **OrderBook Analizi**: Her coin için derinlik tablosu saniyede 10 kez (`100ms`) güncellenerek "duvarlar" (buy/sell walls) tespit edilir.
3.  **İmbalans Hesaplama**: Alış ve satış emirleri arasındaki dengesizlik (Imbalance Ratio) anlık hesaplanarak Kafka'ya iletilir.
4.  **Performans**: Veriler Kafka'ya iletilirken `GZIP` sıkıştırması kullanılarak network trafiği minimize edilir.
