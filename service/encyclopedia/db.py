import os
import pymysql

def get_conn():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "wiki-snake-db"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        database=os.environ.get("DB_NAME", "wiki_snake_storage"),
        port=int(os.environ.get("DB_PORT", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )