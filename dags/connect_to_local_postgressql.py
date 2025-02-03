from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'connect_to_local_postgresql',
    default_args=default_args,
    description='Create and insert data into PostgreSQL table',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS test_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        age INT
    )
    """

    insert_data_sql = """
    INSERT INTO test_table (name, age) VALUES 
    ('John', 30),
    ('Alice', 25),
    ('Bob', 35)
    """

    t1 = PostgresOperator(
        task_id='create_table',
        sql=create_table_sql,
        postgres_conn_id='postgres_test',
        autocommit=True
    )

    t2 = PostgresOperator(
        task_id='insert_data',
        sql=insert_data_sql,
        postgres_conn_id='postgres_test',
        autocommit=True
    )

    t1 >> t2