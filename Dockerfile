FROM python:3.9-bullseye

# 1. Temel Sistem Kütüphaneleri
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless graphviz wget curl procps && \
    apt-get clean;

# 2. Python Bağımlılıkları
RUN pip install --no-cache-dir \
    pyspark==3.4.1 \
    delta-spark==2.4.0 \
    deltalake \
    numpy \
    pandas \
    pyarrow \
    matplotlib \
    seaborn \
    plotly \
    streamlit \
    kafka-python \
    websocket-client \
    requests \
    boto3 \
    minio \
    s3fs \
    psycopg2-binary \
    sqlalchemy \
    fastapi \
    uvicorn \
    python-dotenv \
    mlflow \
    statsmodels \
    scipy \
    yfinance==0.2.33 \
    docker \
    watchdog \
    shap \
    scikit-learn \
    psutil \
    schedule

# 3. JAR DOSYALARI
RUN mkdir -p /opt/spark-jars
WORKDIR /opt/spark-jars

# AWS SDK & Hadoop
RUN wget --no-check-certificate https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.500/aws-java-sdk-bundle-1.12.500.jar && \
    wget --no-check-certificate https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar

# Delta Lake
RUN wget --no-check-certificate https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar && \
    wget --no-check-certificate https://repo1.maven.org/maven2/io/delta/delta-storage/2.4.0/delta-storage-2.4.0.jar

# Kafka & Spark Streaming
RUN wget --no-check-certificate https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar && \
    wget --no-check-certificate https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar && \
    wget --no-check-certificate https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar && \
    wget --no-check-certificate https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# PostgreSQL 
RUN wget --no-check-certificate https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar

# Çalışma dizinine geri dön
WORKDIR /app

#Dosya kopyası docker için
COPY consumer_lake.py .
COPY process_silver.py .
COPY train_model.py .
COPY producer.py .
COPY ingestion_api.py .
COPY batch_processor.py .
COPY universal_producer.py .
COPY ml_watcher.py .
COPY quality_gate.py .
COPY dashboard_app/ ./dashboard_app/
COPY tests/ ./tests/
COPY fake_company.py .
COPY test_generic.py .

CMD ["python", "process_silver.py"]