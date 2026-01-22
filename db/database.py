import sqlite3
from core.logger import setup_logging

logger = setup_logging()


class DataBase:
    def __init__(self, db_path="bank.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def init_database(self):
        con = self.get_connection()
        cursor = con.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number INTEGER PRIMARY KEY,
                bank_code TEXT,
                balance REAL,
                is_active INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number INTEGER,
                bank_code TEXT,
                amount REAL,
                transaction_type TEXT,
                timestamp TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_banks (
                bank_code TEXT PRIMARY KEY,
                ip_address TEXT,
                port INTEGER,
                last_seen TIMESTAMP,
                is_active INTEGER
            )
        """)

        con.commit()
        con.close()
        logger.info("Database initialized")