import os
import requests
import json
import pandas as pd
from tqdm import tqdm
from support.config import TTBKEY

CategoryId = [
    351, 2630, 2643, 2632, 2672, 2669, 7439, 2633, 2673, 2648, 2655, 2645, 55977, 55981, 55978,
    55979, 55055, 55057, 55056, 2599, 2607, 2602, 2601, 2606, 2608, 2600, 6348, 2663, 2665, 2662,
    7395, 2661, 6163, 6165, 2666, 6355, 128622, 128624, 128623, 2719, 2737, 6794, 2744, 2724, 2732,
    2735, 3239, 2721, 5056, 5058, 5059, 5061, 5063, 6576, 6577, 6578, 7396, 6589, 2756, 7411, 427,
    6593, 2065, 2509, 2510, 2684, 1714, 2753, 6188, 35322, 6627, 2687, 6720, 437, 6356, 6358, 6360,
    6361, 6362, 6365, 6989, 2502, 6734, 6357, 14605, 6350, 6385, 6386, 7397, 35323, 2704, 6351,
    15778, 6353, 6352, 6437, 479, 6892, 2836, 6995, 6996, 6997, 12984, 485, 2999, 2847, 7013, 7012,
    7014, 6891, 483, 486, 7006, 7007, 5581, 68185, 36134, 6636, 2835, 6436, 2839, 2838, 2349, 2413,
    2757, 2350, 363, 6369, 387, 6381, 2767, 2765, 49733, 2770, 2773, 2766, 2613, 6346, 6889, 6890,
    2615, 3023, 2621
]


def make_data(cid, start, max_results, ttbkey=TTBKEY, QueryType="Bestseller"):
    url = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"
    params = {
        "TTBKey": ttbkey,
        "QueryType": QueryType,
        "Version": "20131101",
        "SearchTarget": "Book",
        "CategoryId": cid,
        "start": start,
        "MaxResults": max_results,
        "output": "js",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        # print(f"응답 데이터: {response.text}")
        # print(f"HTTP 응답 상태 코드: {response.status_code}")  # 상태 코드 확인
        # response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        data = response.json()  # JSON 데이터 파싱
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"API 호출 오류: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    if "item" in data:
        items = [
            {
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
            for item in data["item"]
        ]
        return pd.DataFrame(items)
    else:
        print("API 호출 성공, 그러나 반환된 데이터가 없습니다.")
        return pd.DataFrame()  # 빈 데이터프레임 반환


def db_update(CategoryId=CategoryId, **kwargs):
    df = pd.DataFrame(columns=[
        "title", "link", "author", "pubDate", "description", "isbn", "isbn13",
        "itemId", "priceSales", "priceStandard", "categoryId", "categoryName",
        "publisher", "customerReviewRank",
    ])

    start = 1
    max_results_per_call = 50

    for cid in tqdm(CategoryId):
        new_data = make_data(cid, start=start, max_results=max_results_per_call)

        if new_data.empty:
            print(f"카테고리 ID : {cid} . 데이터 수집이 중단되었습니다. (API 호출 실패 또는 데이터 부족)")
        else:
            df = pd.concat([df, new_data]).drop_duplicates(subset=["itemId"], ignore_index=True)

    kwargs['ti'].xcom_push(key='db', value=df.to_json())

    return df
