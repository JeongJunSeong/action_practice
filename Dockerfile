FROM python:3.8-slim

ENV AIRFLOW_HOME=/usr/local/airflow


# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y gcc libc-dev vim && \
    rm -rf /var/lib/apt/lists/*


# requirements.txt 복사
COPY requirements.txt $AIRFLOW_HOME/requirements.txt

RUN pip install apache-airflow && \
    pip install --no-cache-dir -r $AIRFLOW_HOME/requirements.txt

RUN mkdir -p $AIRFLOW_HOME
WORKDIR $AIRFLOW_HOME
RUN airflow db init

COPY recommend_dag.py $AIRFLOW_HOME/dags/

EXPOSE 8080

CMD airflow webserver -p 8080 & airflow scheduler