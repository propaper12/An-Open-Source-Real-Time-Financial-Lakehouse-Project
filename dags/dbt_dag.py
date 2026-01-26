dbt_run = BashOperator(
    task_id='dbt_dönüsümleri_tetikle',
<<<<<<< HEAD
    bash_command='docker exec dbt_container dbt run', 
=======
    bash_command='docker exec dbt_container dbt run', # dbt konteyner adı
>>>>>>> cda2fd09ebf927cfc7e32d5c77b558c212d4f57c
    dag=dag,
)