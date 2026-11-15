import psycopg2
from config import DB_CONFIG


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def run_sql_file(path):
    with get_connection() as conn:
        with conn.cursor() as cur:
            with open(path, "r", encoding="utf-8") as file:
                cur.execute(file.read())
