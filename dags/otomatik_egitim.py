from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'mlops_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
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

    train_model >> dbt_transform