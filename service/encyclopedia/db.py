import os
import pymysql

def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "wiki-snake-db"),
        user=os.getenv("DB_USER", "wiki"),
        password=os.getenv("DB_PASS", "wiki"),
        database=os.getenv("DB_NAME", "wiki_snake_storage"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )