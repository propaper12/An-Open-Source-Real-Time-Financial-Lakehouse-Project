# 🚀 Real-Time Financial Lakehouse & MLOps Platform

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-Streaming_%26_ML-orange?style=for-the-badge&logo=apachespark&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-Event_Streaming-black?style=for-the-badge&logo=apachekafka&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-Storage-adventure?style=for-the-badge&logo=delta&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-Orchestration-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)

## 📖 Project Overview

**Real-Time Financial Lakehouse**, kripto para piyasalarından ve finansal API'lerden gelen yüksek hacimli veriyi milisaniyeler içinde işleyen, **Delta Lake** mimarisinde saklayan ve **Spark ML** ile canlı fiyat tahmini yapan uçtan uca (End-to-End) bir büyük veri projesidir.

Bu proje, geleneksel veri ambarı (Data Warehouse) ile veri gölü (Data Lake) kavramlarını birleştiren **Lakehouse** mimarisi üzerine kurulmuştur.

### 🌟 Key Features
* **Hybrid Ingestion:** WebSocket (Binance) ve REST API üzerinden eş zamanlı veri alımı.
* **Real-Time ML Inference:** Spark Streaming üzerinde çalışan modeller ile anlık fiyat tahmini.
* **ACID Transactions:** MinIO üzerinde Delta Lake formatı ile veri bütünlüğü ve Time Travel yeteneği.
* **MLOps Pipeline:** Airflow ile modellerin performans takibi ve otomatik yeniden eğitilmesi (Retraining).
* **Interactive Dashboard:** Streamlit ile sistem sağlığı, canlı veriler ve Docker konteyner yönetimi.

---

## 🏗️ Architecture

The system consists of 5 main layers managed by Docker Compose:

1.  **Ingestion:** `producer.py` listens to Binance WebSockets; `ingestion_api.py` accepts HTTP POST requests. Data is buffered in **Kafka**.
2.  **Stream Processing:** **Spark Structured Streaming** reads from Kafka, performs aggregations, applies ML models, and writes to MinIO (Bronze/Silver).
3.  **Storage (Lakehouse):**
    * **Bronze Layer:** Raw data (Delta format).
    * **Silver Layer:** Cleaned, enriched data with ML predictions.
    * **Gold Layer:** Business-level aggregates (via dbt).
4.  **Serving:** Processed data is written to **PostgreSQL** for low-latency querying.
5.  **Orchestration & Monitoring:** **Airflow** manages workflows; **Streamlit** provides the UI.

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose
* Python 3.9+ (Optional, for local development)
* Git

### 1. Installation
Clone the repository:
```bash
git clone [https://github.com/your-username/financial-lakehouse.git](https://github.com/your-username/financial-lakehouse.git)
cd financial-lakehouse
2. Build & RunStart the entire stack with a single command. This will pull images and build custom containers:Bashdocker-compose up -d --build
(Note: Initial startup may take 5-10 minutes depending on your internet connection.)3. Verify InstallationCheck if all containers are running:Bashdocker-compose ps
🔌 Service Endpoints (Localhost Connections)Once the system is up, you can access the interfaces via your browser. All necessary credentials are listed below:ServiceURLCredentials (User/Pass)DescriptionStreamlit Dashboardhttp://localhost:8501N/AMain Control Plane & AnalyticsMinIO Consolehttp://localhost:9001admin / admin12345S3 Object Storage BrowserAirflow UIhttp://localhost:8081admin / adminWorkflow OrchestrationMetabasehttp://localhost:3000Setup RequiredBI & Visualization ToolSpark Masterhttp://localhost:8080N/ASpark Cluster StatusFastAPI Docshttp://localhost:8000/docsN/AAPI Swagger UI🛠️ Operational Guide (How to Use)1. Triggering Model Retraining (MLOps)The system trains models automatically via Airflow, but you can trigger it manually:Option A: Via DashboardGo to http://localhost:8501 and click the "🚀 Modeli Yeniden Eğit" button in the sidebar.Option B: Via TerminalExecute the training script inside the Spark container:Bashdocker exec -it spark-silver python train_model.py
2. Running Transformations (dbt)To update the Gold layer tables manually:Bashdocker exec -it dbt_transformer dbt run
3. Simulating External DataIf the markets are slow, you can simulate a fake company sending data via API:Bash# Run locally or in a separate container
python fake_company.py
📂 Project StructurePlaintext├── dags/                   # Airflow DAGs (MLOps pipelines)
├── dbt_project/            # dbt models for Gold Layer
├── ingestion_api.py        # FastAPI Gateway source code
├── producer.py             # Binance WebSocket producer
├── process_silver.py       # Spark Streaming & Inference logic
├── consumer_lake.py        # Bronze Layer ingestion logic
├── train_model.py          # ML Training script (RandomForest, LinearReg)
├── dashboard.py            # Streamlit Control Plane
├── docker-compose.yaml     # Infrastructure definition
└── requirements.txt        # Python dependencies
🔧 TroubleshootingKafka Connection Error: Wait 30 seconds after startup. Kafka takes time to elect a leader.Dashboard Slow? The dashboard uses caching. First load might take 5-10 seconds as it connects to Docker socket."OOMKilled" (Out of Memory): This stack requires at least 8GB RAM. If containers crash, try increasing Docker Desktop memory limit to 8GB or 12GB.🤝 ContributingContributions are welcome! Please feel free to submit a Pull Request.Fork the projectCreate your feature branch (git checkout -b feature/AmazingFeature)Commit your changes (git commit -m 'Add some AmazingFeature')Push to the branch (git push origin feature/AmazingFeature)Open a Pull Request📝 LicenseDistributed under the MIT License. See LICENSE for more information.<p align="center"><b>Developed by Ömer Çakan</b>Data Engineer & Big Data Enthusiast</p>
