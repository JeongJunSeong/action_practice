from airflow.providers.mysql.hooks.mysql import MySqlHook
import pandas as pd

def save_books_to_database(df, connection_id):
    # Create a MySQL table with UNIQUE constraints to prevent duplicates
    create_table_query = """
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        link TEXT,
        author VARCHAR(255),
        pubDate VARCHAR(50),
        description TEXT,
        isbn VARCHAR(50),
        isbn13 VARCHAR(50),
        itemId VARCHAR(50),
        priceSales FLOAT,
        priceStandard FLOAT,
        categoryId VARCHAR(50),
        categoryName VARCHAR(255),
        publisher VARCHAR(255),
        customerReviewRank FLOAT,
        UNIQUE (isbn13)  -- Ensure no duplicate records based on isbn13
    );
    """

    # Filter out rows where description is empty or NaN
    df = df[df['description'].notna() & (df['description'] != '')]

    # Convert DataFrame to list of tuples and handle NaN values
    data = df.fillna('').applymap(lambda x: str(x) if not isinstance(x, (int, float)) else f"{x:.2f}").values.tolist()

    # Define INSERT ON DUPLICATE KEY UPDATE query
    insert_query = """
    INSERT INTO books (
        title, link, author, pubDate, description, isbn, isbn13, itemId,
        priceSales, priceStandard, categoryId, categoryName, publisher, customerReviewRank
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        title=VALUES(title),
        link=VALUES(link),
        author=VALUES(author),
        pubDate=VALUES(pubDate),
        description=VALUES(description),
        isbn=VALUES(isbn),
        itemId=VALUES(itemId),
        priceSales=VALUES(priceSales),
        priceStandard=VALUES(priceStandard),
        categoryId=VALUES(categoryId),
        categoryName=VALUES(categoryName),
        publisher=VALUES(publisher),
        customerReviewRank=VALUES(customerReviewRank)
    """

    mysql_hook = MySqlHook(
        host="mariadb",
        schema="book_db",
        ser="airflow",
        password="airflow",
        port=3306
    )

    # 테이블 생성
    mysql_hook.run(create_table_query)

    # MySQL Connection 객체를 가져와 데이터 삽입
    connection = mysql_hook.get_conn()
    cursor = connection.cursor()
    try:
        cursor.executemany(insert_query, data)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def save_books_to_database_task(**kwargs):
    ti = kwargs['ti']
    df_json = ti.xcom_pull(key='db', task_ids='db_update')
    if df_json is not None:
        df = pd.read_json(df_json)
        # MySQL에 책 정보 저장
        save_books_to_database(df, 'book_db')
    else:
        print("데이터를 가져오는데 실패했습니다.")