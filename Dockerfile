FROM python:3.9-bullseye

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

WORKDIR /app

COPY consumer_lake.py .
COPY process_silver.py .
COPY train_model.py .
COPY producer.py .
COPY dashboard.py .
COPY ingestion_api.py .

CMD ["python", "consumer_lake.py"]