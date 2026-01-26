FROM python:3.9-bullseye

<<<<<<< HEAD
# 1. Temel Sistem Kütüphaneleri (Java 11 Spark için şart)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless graphviz wget curl procps && \
    apt-get clean;

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
    scikit-learn\
    psutil

WORKDIR /usr/local/lib/python3.9/site-packages/pyspark/jars/
RUN wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar && \
    wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.500/aws-java-sdk-bundle-1.12.500.jar && \
    wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar
=======
# Java (Spark için) ve Graphviz (Mimari şeması için)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless graphviz && \
    apt-get clean;

# Python Kütüphaneleri
# Not: Airflow bağlantısı için 'requests' eklendi.
RUN pip install --no-cache-dir \
    pyspark==3.4.1 \
    numpy \
    pandas \
    matplotlib \
    delta-spark==2.4.0 \
    deltalake \
    websocket-client \
    kafka-python \
    streamlit \
    plotly \
    s3fs \
    psutil \
    graphviz \
    psycopg2-binary \
    sqlalchemy \
    docker \
    fastapi \
    uvicorn \
    mlflow \
    boto3 \
    requests \
    statsmodels \
    scipy \
    minio
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c

WORKDIR /app

COPY consumer_lake.py .
COPY process_silver.py .
COPY train_model.py .
COPY producer.py .
<<<<<<< HEAD
COPY dashboard_app/ ./dashboard_app/
COPY ingestion_api.py .
COPY batch_processor.py . 
COPY fake_company.py .
COPY universal_producer.py .
=======
COPY dashboard.py .
COPY ingestion_api.py .
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c

CMD ["python", "consumer_lake.py"]