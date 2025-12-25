# 🚀 Real-Time Financial Lakehouse & MLOps Platform

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-Streaming_%26_ML-orange?style=for-the-badge&logo=apachespark&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-Event_Streaming-black?style=for-the-badge&logo=apachekafka&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-Storage-adventure?style=for-the-badge&logo=delta&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-Orchestration-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)

## 📖 Project Overview

**Real-Time Financial Lakehouse** is an end-to-end Big Data project that processes high-volume crypto market data in milliseconds, stores it in **Delta Lake** architecture, and performs real-time price predictions using **Spark ML**.

This project implements the **Modern Data Stack (MDS)** principles, combining the best of Data Warehouses and Data Lakes into a unified Lakehouse architecture running entirely on Docker.

### 🌟 Key Features
* **Hybrid Ingestion:** Simultaneous data ingestion via WebSocket (Binance) and REST API.
* **Real-Time ML Inference:** Live price prediction using pre-trained Spark ML models on streaming data.
* **ACID Transactions:** Data integrity and Time Travel capabilities using Delta Lake on MinIO.
* **MLOps Pipeline:** Automated model monitoring and retraining workflows managed by Airflow.
* **Interactive Dashboard:** A comprehensive control plane built with Streamlit to monitor system health, live data, and Docker containers.

---

## 🏗️ Architecture

The system consists of 5 main layers managed by Docker Compose:

1.  **Ingestion Layer:**
    * `producer.py`: Listens to Binance WebSockets for live trade data.
    * `ingestion_api.py`: FastAPI gateway for accepting external POST requests.
    * **Kafka:** Buffers high-velocity data before processing.
2.  **Stream Processing:**
    * **Spark Structured Streaming:** Reads from Kafka, performs windowed aggregations, and applies ML models.
3.  **Storage (The Lakehouse):**
    * **Bronze Layer:** Raw data stored in Delta format.
    * **Silver Layer:** Cleaned, enriched data with ML predictions.
    * **Gold Layer:** Business-level aggregates transformed via **dbt**.
4.  **Serving Layer:**
    * **PostgreSQL:** Low-latency database for serving processed data to the dashboard.
5.  **Orchestration & UI:**
    * **Airflow:** Manages batch jobs and MLOps pipelines.
    * **Streamlit:** Provides a real-time analytics dashboard and system control.

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose
* Git
* 8GB+ RAM recommended



### 1. Installation
Clone the repository:
bash
git clone [https://github.com/your-username/financial-lakehouse.git](https://github.com/your-username/financial-lakehouse.git)
cd financial-lakehouse
### 2. Build & Run
Start the entire stack with a single command. This will pull images and build custom containers:

Bash

docker-compose up -d --build
3. Verify Installation
Check if all containers are running:

Bash

docker-compose ps
| Service             | URL                                                      | Credentials (User/Pass) | Description                    |
| ------------------- | -------------------------------------------------------- | ----------------------- | ------------------------------ |
| Streamlit Dashboard | [http://localhost:8501](http://localhost:8501)           | N/A                     | Main Control Plane & Analytics |
| MinIO Console       | [http://localhost:9001](http://localhost:9001)           | admin / admin12345      | S3 Object Storage Browser      |
| Airflow UI          | [http://localhost:8081](http://localhost:8081)           | admin / admin           | Workflow Orchestration         |
| Metabase            | [http://localhost:3000](http://localhost:3000)           | Setup Required          | BI & Visualization Tool        |
| Spark Master        | [http://localhost:8080](http://localhost:8080)           | N/A                     | Spark Cluster Status           |
| FastAPI Docs        | [http://localhost:8000/docs](http://localhost:8000/docs) | N/A                     | API Swagger UI                 |
Operational Guide
1. Triggering Model Retraining (MLOps)
The system trains models automatically via Airflow, but you can trigger it manually:

Option A (GUI): Go to the Dashboard (https://www.google.com/search?q=http://localhost:8501) and click "🚀 Modeli Yeniden Eğit".

Option B (CLI):

Bash

docker exec -it spark-silver python train_model.py
2. Running Transformations (dbt)
To update the Gold layer tables manually:

Bash

docker exec -it dbt_transformer dbt run
3. Simulating External Data
To simulate a fake company sending data to the API:

Bash

python fake_company.py
📂 Project Structure
├── dags/                   # Airflow DAGs (MLOps pipelines)
├── dbt_project/            # dbt models for Gold Layer transformation
├── ingestion_api.py        # FastAPI Gateway source code
├── producer.py             # Binance WebSocket producer
├── process_silver.py       # Spark Streaming & Inference logic
├── consumer_lake.py        # Bronze Layer ingestion logic
├── train_model.py          # ML Training script (RandomForest, LinearReg)
├── dashboard.py            # Streamlit Control Plane
├── docker-compose.yaml     # Infrastructure definition
└── requirements.txt        # Python dependencies
🔧 Troubleshooting
Kafka Connection Error: Kafka takes about 30-60 seconds to elect a leader after startup. If the producer fails, wait a minute and restart it.

Dashboard Slow Loading: The dashboard caches data to improve performance. The first load might take a few seconds as it connects to the Docker socket.

"OOMKilled" (Out of Memory): This stack runs many services (Kafka, Spark, Postgres). If containers crash, ensure your Docker Desktop has at least 8GB RAM allocated.

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the project

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📝 License
Distributed under the MIT License. See LICENSE for more information.

<p align="center"> <b>Developed by Ömer Çakan</b>


Data Engineer & Big Data Enthusiast </p>
