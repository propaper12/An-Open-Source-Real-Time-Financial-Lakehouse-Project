dbt_run = BashOperator(
    task_id='dbt_dönüsümleri_tetikle',
    bash_command='docker exec dbt_container dbt run', # dbt konteyner adı
    dag=dag,
)