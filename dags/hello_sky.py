from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

# DAG 정의
dag = DAG(
    'hello_sky_dag',
    description='Prints "Hello, sky" using BashOperator',
    schedule_interval=None,  # DAG는 수동으로 트리거됨
    start_date=datetime(2024, 1, 1),  # DAG 실행의 시작일
    catchup=False  # 이전 실행을 캐치업하지 않음
)

# BashOperator를 사용하여 "Hello, sky"를 출력하는 task 정의
print_hello = BashOperator(
    task_id='print_hello',
    bash_command='echo "Hello, sky"',
    dag=dag
)

print_current_time = BashOperator(
    task_id='print_current_time',
    bash_command='echo "Current time: $(date)"',
    dag=dag
)

print_execution_time = BashOperator(
    task_id='print_execution_time',
    bash_command='echo "Execution time: {{ execution_date }}"',
    dag=dag
)

# task 간의 의존성 설정
print_hello >> print_current_time >> print_execution_time