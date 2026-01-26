from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
<<<<<<< HEAD
    'owner': 'mlops_engineer',
    'retries': 1,
=======
    'owner': 'data_engineer',
    'retries': 2,
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c
    'retry_delay': timedelta(minutes=5),
}

with DAG(
<<<<<<< HEAD
    'crypto_data_pipeline_v2',  
    default_args=default_args,
    description='AutoML Training Engine & Reporting',
    schedule_interval=None,  
    start_date=datetime(2023, 12, 1),
    catchup=False,
    tags=['production', 'automl', 'spark']
) as dag:
    target_symbol = "{{ dag_run.conf.get('symbol', 'ALL') }}"
    
    spark_cmd = f"docker exec spark-silver python /app/train_model.py {target_symbol}"

    train_model = BashOperator(
        task_id='trigger_automl_engine',
        bash_command=spark_cmd
    )
    dbt_transform = BashOperator(
        task_id='update_analytics_tables',
        bash_command='docker exec dbt_transformer dbt run',
        trigger_rule='all_success' 
    )

=======
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
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c
    train_model >> dbt_transform