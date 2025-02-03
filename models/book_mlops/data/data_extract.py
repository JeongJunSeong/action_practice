# Define the functions
import requests
import pandas as pd
import json
import os

def search_books(ttbkey, query, df, queryType="Keyword", start=1, MaxResults=50, sort="Accuracy"):
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ttbkey,
        "Query": query,
        "QueryType": queryType,
        "start": start,
        "MaxResults": MaxResults,
        "Sort": sort,
        "Cover": "None",
        "CategoryId": "0",
        "output": "js",
        "SearchTarget": "Book",
        "Version": "20131101",
        "outofStockfilter": 1,
        "RecentPublishFilter": 0,
    }

    response = requests.get(url, params=params)
    data = json.loads(response.text)

    if "item" in data:
        items = []
        for item in data["item"]:
            book_info = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "author": item.get("author", ""),
                "pubDate": item.get("pubDate", ""),
                "description": item.get("description", ""),
                "isbn": item.get("isbn", ""),
                "isbn13": item.get("isbn13", ""),
                "itemId": item.get("itemId", ""),
                "priceSales": item.get("priceSales", ""),
                "priceStandard": item.get("priceStandard", ""),
                "categoryId": item.get("categoryId", ""),
                "categoryName": item.get("categoryName", ""),
                "publisher": item.get("publisher", ""),
                "customerReviewRank": item.get("customerReviewRank", ""),
            }
            items.append(book_info)

        df = pd.concat([df, pd.DataFrame(items)], ignore_index=True)

    return df


def collect_books(ttbkey, query, max_books=500):
    df = pd.DataFrame(columns=[
        "title", "link", "author", "pubDate", "description", "isbn", "isbn13",
        "itemId", "priceSales", "priceStandard", "categoryId", "categoryName",
        "publisher", "customerReviewRank",
    ])

    start = 1
    max_results_per_call = 50

    while len(df) < max_books:
        df = search_books(ttbkey, query, df, start=start, MaxResults=max_results_per_call)
        start += 1
        if len(df) == len(df.drop_duplicates()):
            break

    df = df.head(max_books)
    return df


def search_and_collect_books(**kwargs):
    ttbkey = kwargs['params']['ttbkey']
    query = kwargs['params']['query']
    collected_books = collect_books(ttbkey, query)

    # 저장 경로 설정
    save_path = '/opt/airflow/data/'

    # 디렉토리가 없으면 생성
    os.makedirs(save_path, exist_ok=True)

    # 파일명 설정 (쿼리와 현재 날짜를 포함)
    file_name = f"books_{query}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    full_path = os.path.join(save_path, file_name)

    # DataFrame을 JSON 파일로 저장
    collected_books.to_json(full_path, orient='records', force_ascii=False, indent=4)

    print(f"Data saved to {full_path}")

    kwargs['ti'].xcom_push(key='saved_books_path', value=full_path)
