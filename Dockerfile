# Python 3.9 기반의 Airflow 공식 이미지 사용
FROM apache/airflow:2.7.2-python3.9

# 루트 사용자로 전환
USER root

RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libmariadb-dev

# airflow 사용자로 돌아가기
USER airflow

# login 정보
COPY .env /opt/airflow/.env
# variable 정보
COPY variables.json /opt/airflow/config/variables.json

# 패키지 다운로드
COPY requirements.txt /opt/airflow/requirements.txt

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt
RUN pip install --no-cache-dir apache-airflow-providers-openlineage==1.8.0

# 작업 디렉토리와 기타 필요한 파일들 복사
COPY ./dags /opt/airflow/dags
COPY ./models /opt/airflow/models
COPY ./support /opt/airflow/support

RUN airflow db init

EXPOSE 8080

# variable 등록
RUN airflow variables import /opt/airflow/config/variables.json

# connection 정보
ENV AIRFLOW_CONN_BOOK_DB='mysql://user:password@host:3306/dbname'


CMD airflow webserver -p 8080 & airflow scheduler

