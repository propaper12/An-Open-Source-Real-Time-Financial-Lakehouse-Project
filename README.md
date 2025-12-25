# 🚀 Real-Time Financial Lakehouse & MLOps Platform

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-Streaming_%26_ML-orange?style=for-the-badge&logo=apachespark&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-Event_Streaming-black?style=for-the-badge&logo=apachekafka&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-Storage-adventure?style=for-the-badge&logo=delta&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Interactive_Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

## 📖 Project Overview (Proje Özeti)

**Real-Time Financial Lakehouse**, kripto para piyasalarından (Binance) ve simüle edilmiş şirket API'lerinden akan veriyi milisaniyeler içinde işleyen, analiz eden ve yapay zeka modelleriyle anlık fiyat tahmini yapan uçtan uca (End-to-End) bir büyük veri projesidir.

Bu proje, **Modern Data Stack (MDS)** prensiplerine uygun olarak; Lambda mimarisi yerine **Lakehouse** mimarisi üzerine kurulmuştur. Veri ingestion, stream processing, machine learning inference ve raporlama katmanlarını tek bir Docker ortamında birleştirir.

---

## 🏗️ Architecture (Mimari)

Proje, verinin yolculuğunu 5 ana katmanda ele alır:

1.  **Ingestion Layer:**
    * **Binance WebSocket:** Canlı BTC/USDT ticaret verilerini (Trade Streams) anlık olarak yakalar.
    * **FastAPI Gateway:** Harici kaynaklardan gelen POST isteklerini karşılar ve Kafka'ya iletir.
    * **Apache Kafka:** Yüksek hacimli veriyi tamponlamak (buffering) için mesaj kuyruğu olarak çalışır.

2.  **Storage Layer (The Lakehouse):**
    * **MinIO (S3 Compatible):** Veriler **Delta Lake** formatında (Bronze, Silver, Gold katmanları) saklanır.
        * *Bronze:* Ham veri (Raw).
        * *Silver:* Temizlenmiş, zenginleştirilmiş ve ML tahmini yapılmış veri.
        * *Gold:* İş analitiğine hazır, dbt ile dönüştürülmüş veri.

3.  **Processing & ML Layer:**
    * **Apache Spark Streaming:** Kafka'dan okunan veriyi işler.
    * **Spark MLlib:** Eğitilmiş modelleri (Random Forest, Linear Regression) belleğe yükler ve akan veriye canlı olarak fiyat tahmini (Inference) yapar.
    * **MLOps:** Airflow ile modellerin performansını izler ve otomatik yeniden eğitim (Retraining) süreçlerini yönetir.

4.  **Serving & BI Layer:**
    * **PostgreSQL:** Düşük gecikmeli sorgular için sonuçların yazıldığı operasyonel veritabanı.
    * **Streamlit Dashboard:** Sistemin canlı izlendiği, Docker konteynerlarının yönetildiği ve analizlerin sunulduğu kontrol paneli.

---

## 🛠️ Tech Stack (Teknoloji Yığını)

| Category | Technologies |
|----------|--------------|
| **Language** | Python 3.9, SQL |
| **Ingestion** | Apache Kafka, WebSocket, FastAPI |
| **Processing** | Apache Spark (PySpark), Spark Streaming |
| **Storage** | MinIO (S3), Delta Lake, PostgreSQL |
| **Orchestration** | Apache Airflow, Docker Compose |
| **Transformation** | dbt (Data Build Tool) |
| **Visualization** | Streamlit, Plotly |
| **DevOps** | Docker, Git |

---

## 🚀 Installation & Setup (Kurulum)

Bu projeyi yerel makinenizde çalıştırmak için **Docker** ve **Docker Compose** yüklü olmalıdır.

### 1. Projeyi Klonlayın
```bash
git clone [https://github.com/kullaniciadi/financial-lakehouse.git](https://github.com/kullaniciadi/financial-lakehouse.git)
cd financial-lakehouse
