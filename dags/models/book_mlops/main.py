import pendulum
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator

from support.config import TTBKEY
from models.book_mlops.data.db_update import db_update
from models.book_mlops.data.save_books_to_database import save_books_to_database_task
from models.book_mlops.data.data_extract import search_and_collect_books
from models.book_mlops.data.json_to_db import json_to_db
from models.book_mlops.model.new_model_create import new_model_create
from models.book_mlops.model.predict import predict

local_timezone = pendulum.timezone('Asia/Seoul')

query = "파이썬"

dag = DAG(dag_id="book_mlops",
          default_args={
              "owner": "insu",
              "depends_on_past": False,
              "email": ["parkinsu9701@gmail.com"],
          },
          description="책 추천 모델",
          # schedule='@daily',
          schedule='0 0 * * *',
          start_date=datetime(2025, 1, 1, tzinfo=local_timezone),
          catchup=False,
          tags=["mlops", "recommend"]
          )

def choose_path(**kwargs):
    if kwargs['dag_run'].run_type == 'scheduled':
        return 'db_update'
    else:
        return 'search_and_collect_books'

branch_task = BranchPythonOperator(
    task_id='branch_task',
    python_callable=choose_path,
    dag=dag,
)

# Define the tasks
db_update = PythonOperator(
    task_id='db_update',
    python_callable=db_update,
    dag=dag,
)

save_books_to_database_task = PythonOperator(
    task_id="save_books_to_database",
    python_callable=save_books_to_database_task,
    trigger_rule="none_failed_min_one_success",
    dag=dag,
)

new_model_create = PythonOperator(
    task_id="new_model_create",
    python_callable=new_model_create,
    dag=dag,
)

search_task = PythonOperator(
    task_id='search_and_collect_books',
    python_callable=search_and_collect_books,
    op_kwargs={'params': {'ttbkey': TTBKEY, 'query': query}},
    trigger_rule='all_done',
    dag=dag,
)

predict_task = PythonOperator(
    task_id="predict",
    python_callable=predict,
    op_kwargs={'params': {'query': query}},
    dag=dag,
)

json_to_db = PythonOperator(
    task_id='json_to_db',
    python_callable=json_to_db,
    dag=dag,
)

branch_task >> [db_update, search_task]
db_update >> save_books_to_database_task >> json_to_db >> new_model_create
search_task >> predict_task