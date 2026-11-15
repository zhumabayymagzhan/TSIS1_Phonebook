import os

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "phonebook_db"),
    "user": os.getenv("PGUSER", "zhumabaymagzhan"),
    "password": os.getenv("PGPASSWORD", ""),
}
