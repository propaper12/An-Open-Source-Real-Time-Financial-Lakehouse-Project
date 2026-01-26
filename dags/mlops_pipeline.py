from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
from docker.types import Mount

default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'crypto_mlops_retraining',
    default_args=default_args,
    schedule_interval='0 3 * * *', # Her gece 03:00
    start_date=datetime(2023, 1, 1),
    catchup=False
) as dag:

    train_model = DockerOperator(
        task_id='train_new_model',
        image='projenin_adi-spark-silver:latest',
        api_version='auto',
        auto_remove=True,
        command='python train_model.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='data-network',
        mounts=[
            Mount(source='/home/kullanici/proje/checkpoints_silver', target='/app/checkpoints_silver', type='bind'), 
        ]
    )
 