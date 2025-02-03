import os
import json
import pandas as pd

from models.book_mlops.data.save_books_to_database import save_books_to_database

def json_to_db(**kwargs):
    # 저장 경로 설정
    save_path = '/opt/airflow/data/'

    # 디렉토리 내의 모든 JSON 파일 찾기
    json_files = [f for f in os.listdir(save_path) if f.endswith('.json')]

    for json_file in json_files:
        file_path = os.path.join(save_path, json_file)

        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # DataFrame으로 변환
        df = pd.DataFrame(data)

        # MySQL에 책 정보 저장
        save_books_to_database(df, 'book_db')

        # 처리된 파일 삭제 (선택사항)
        os.remove(file_path)

    print(f"Processed and saved {len(json_files)} JSON files to the database.")
