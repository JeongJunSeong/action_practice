# 추후에 log출력하는 코드는 주석처리해서 사용할 예정입니다.
# 20250121 Airflow 공식문서 기준으로 설치하였을 때 동작하는 것까지 확인함.
import json
import requests
import pandas as pd
import os
import re

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.log.logging_mixin import LoggingMixin
from datetime import datetime, timedelta
from airflow.models import Variable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def search_books(query, ttbkey="ttbedisonkyj1859001", start=1, max_results=50):
    """API에서 책 데이터를 검색하는 함수"""
    logger = LoggingMixin().log
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey":ttbkey,
        "Query": query,
        "QueryType": "Keyword",
        "start": start,
        "MaxResults": max_results,
        "Sort": "Accuracy",
        "output": "js",
        "SearchTarget": "Book",
    }
    response = requests.get(url, params=params)
    logger.info(f"API 응답 상태 코드: {response.status_code}")
    logger.info(f"응답 데이터 미리보기: {response.text[:200]}")
    try:
        c_data = re.sub(r';\s*$', '',response.text)
        data = json.loads(c_data)
        return data.get("item", [])
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        logger.error(f"응답 데이터: {response.text}")
        return []
    
    
def collect_books(**kwargs):
    """책 데이터를 여러 페이지에서 수집"""
    logger = LoggingMixin().log
    logger.info("데이터 수집 시작")
    try:
        # Airflow 홈 디렉토리 내 데이터 저장 경로 설정
        import os
        from airflow.configuration import conf
        
        data_dir = os.path.join(conf.get('core', 'dags_folder'), 'tmp')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"tmp 디렉토리 생성: {data_dir}")
        
        # 저장 경로 권한 확인
        logger.info(f"저장 경로 권한 확인: {os.access(data_dir, os.W_OK)}")

        query = "파이썬"
        max_books = 100
        all_books = []
        start = 1

        logger.info(f"검색 시작: 키워드={query}, 최대 책 수={max_books}")

        while len(all_books) < max_books:
            logger.info(f"현재 페이지: {start}, 수집된 책 수: {len(all_books)}")
            books = search_books(query, start=start)
            logger.info(f"현재 페이지에서 수집된 책 수: {len(books) if books else 0}")
            
            if not books:
                logger.info("더 이상 수집할 책이 없습니다.")
                break
            all_books.extend(books)
            start += len(books)
        if not all_books:
            logger.error("수집된 도서 데이터가 없습니다")
            raise ValueError("No books collected")
        
        df = pd.DataFrame(all_books)
        if df.empty:
            logger.error("DataFrame이 비어있습니다")
            raise ValueError("Empty DataFrame")
        logger.info(f"DataFrame 생성 완료. shape: {df.shape}, columns: {df.columns.tolist()}")
        
        # 파일 저장 경로 설정
        file_path = os.path.join(data_dir, 'book_data.csv')
        df.to_csv(file_path, index=False)
        logger.info(f"CSV 파일 저장 완료: {file_path}")
        
        # 파일 존재 여부 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"저장된 파일 크기: {file_size} bytes")
        
        kwargs['ti'].xcom_push(key='book_data_path', value=file_path)
        logger.info("XCom 데이터 저장 완료")

    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        raise



def recommend_books(**kwargs):
    """TF-IDF 벡터화 및 KMeans 클러스터링을 활용한 책 추천"""
    logger = LoggingMixin().log
    try:
        # Airflow 홈 디렉토리 내 데이터 저장 경로 설정
        import os
        from airflow.configuration import conf
        
        data_dir = os.path.join(conf.get('core', 'dags_folder'), 'tmp')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"tmp 디렉토리 생성: {data_dir}")

        ti = kwargs['ti']
        book_data_path = ti.xcom_pull(task_ids='collect_books_task', key='book_data_path')
        
        if not os.path.exists(book_data_path):
            logger.error(f"파일이 존재하지 않습니다: {book_data_path}")
            raise FileNotFoundError(f"File not found: {book_data_path}")
            
        df = pd.read_csv(book_data_path)
        
        if df.empty:
            logger.error("CSV 파일이 비어있습니다")
            raise ValueError("Empty CSV file")
        
        if 'description' not in df.columns:
            logger.error("description 컬럼이 존재하지 않습니다")
            return
        
        df = df.dropna(subset=['description'])
        tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
        tfidf_matrix = tfidf_vectorizer.fit_transform(df["description"])

        num_clusters = min(len(df) // 10, 20)
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        df["cluster"] = kmeans.fit_predict(tfidf_matrix)

        largest_cluster = df["cluster"].value_counts().idxmax()
        recommended_books = df[df["cluster"] == largest_cluster].head(5)

        # 파일 저장 경로 설정
        file_path = os.path.join(data_dir, 'recommended_books.csv')
        recommended_books.to_csv(file_path, index=False)
        logger.info(f"추천 도서 CSV 파일 저장 완료: {file_path}")
        
        # 파일 존재 여부 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"저장된 파일 크기: {file_size} bytes")
            
        kwargs['ti'].xcom_push(key='recommended_books_path', value=file_path)
        logger.info("XCom 데이터 저장 완료")

    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        raise


def print_recommendations(**kwargs):
    """추천된 책 출력"""
    logger = LoggingMixin().log
    try:
        from airflow.configuration import conf
        
        data_dir = os.path.join(conf.get('core', 'dags_folder'), 'tmp')
        file_path = os.path.join(data_dir, 'recommended_books.csv')
        
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        df = pd.read_csv(file_path)
        print(df[['title', 'author', 'description']])
        
    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        raise


# DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'book_recommendation_pipeline',
    default_args=default_args,
    description='Book Recommendation using Airflow',
    schedule_interval=timedelta(days=1),
)

collect_task = PythonOperator(
    task_id='collect_books_task',
    python_callable=collect_books,
    provide_context=True,
    dag=dag,
)

recommend_task = PythonOperator(
    task_id='recommend_books_task',
    python_callable=recommend_books,
    provide_context=True,
    dag=dag,
)

print_task = PythonOperator(
    task_id='print_recommendations_task',
    python_callable=print_recommendations,
    dag=dag,
)

collect_task >> recommend_task >> print_task
