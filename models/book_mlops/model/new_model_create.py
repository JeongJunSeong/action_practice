from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from airflow.models import Variable
import joblib
import os

airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')

def new_model_create(**kwargs):

    ti = kwargs['ti']
    df_json = ti.xcom_pull(key='db', task_ids='db_update')
    df = pd.read_json(df_json)

    book_descriptions = df["description"].fillna("")

    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(book_descriptions)

    # KMeans 클러스터링
    num_clusters = max(min(len(df) // 10, 20), 1)
    kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    # 모델 저장
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"

    # 모델 경로가 존재하지 않으면 생성
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    joblib.dump(kmeans, model_path)
    joblib.dump(tfidf_vectorizer, tfidf_path)

    return model_path, tfidf_path