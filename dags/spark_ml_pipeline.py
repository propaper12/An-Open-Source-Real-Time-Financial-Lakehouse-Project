from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from docker.types import Mount

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

with DAG(
    dag_id='spark_ml_pipeline',  
    default_args=default_args,
    description='Spark ML Model Egitim Pipeline',
    schedule_interval=None,  
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'spark'],
) as dag:

    train_model = DockerOperator(
        task_id='train_model_task',
        image='real-time-financial-lakehouse-spark-silver:latest', 
        container_name='spark_ml_runner_task',
        api_version='auto',
        auto_remove=True,
        command="python /app/train_model.py {{ dag_run.conf['symbol'] }} {{ dag_run.conf['algorithm'] }}",
        docker_url="unix://var/run/docker.sock",
        network_mode="real-time-financial-lakehouse_data-network", 
        x
        mounts=[
            Mount(source='/c/Users/omerc/OneDrive/Masaüstü/Real-Time Financial Lakehouse/minio_data', target='/data', type='bind'), 
        ],
        environment={
            'SPARK_MASTER': 'local[*]',
            'MINIO_ENDPOINT': 'minio:9000',
            'MINIO_ACCESS_KEY': 'admin',
            'MINIO_SECRET_KEY': 'admin12345'
        }
    )

    train_model