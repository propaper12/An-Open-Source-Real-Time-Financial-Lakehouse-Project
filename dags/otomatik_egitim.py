from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineer',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'crypto_data_pipeline_v2', # İsim güncellendi
    default_args=default_args,
    description='Spark ML Eğitimi ve dbt Gold Layer Dönüşüm Zinciri',
    schedule_interval='0 3 * * *', # Her gece 03:00
    start_date=datetime(2023, 12, 1),
    catchup=False,
    tags=['production', 'lakehouse', 'dbt']
) as dag:

    # 1. Adım: Spark ile Model Eğitimi (Silver Katmanı)
    train_model = BashOperator(
        task_id='spark_ml_train',
        bash_command='docker exec spark-silver python train_model.py'
    )

    # 2. Adım: dbt ile Analitik Tabloların Oluşturulması (Gold Katmanı)
    # Önce modelleri çalıştırır (run), başarılı olursa testleri yapar (test)
    dbt_transform = BashOperator(
        task_id='dbt_gold_transformations',
        bash_command='docker exec dbt_transformer dbt run && docker exec dbt_transformer dbt test'
    )

    # Bağımlılık Zinciri: Önce Eğitim -> Sonra Raporlama
    train_model >> dbt_transform