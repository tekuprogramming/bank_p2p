import sqlite3
from core.logger import setup_core_logging
from typing import List, Dict, Any  #nový

logger = setup_core_logging()   #nový

class DataBase:
    def __init__(self, db_path: str = "bank.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def init_database(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_number INTEGER PRIMARY KEY,
                    bank_code TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(account_number, bank_code)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number INTEGER NOT NULL,
                    bank_code TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_number) REFERENCES accounts(account_number)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS known_banks (
                    bank_code TEXT PRIMARY KEY,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(ip_address, port)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_connections (
                    connection_id TEXT PRIMARY KEY,
                    client_ip TEXT NOT NULL,
                    client_port INTEGER NOT NULL,
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Any:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if fetch:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid
            conn.commit()
            return result
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            conn.close()
    
    def get_all_accounts(self) -> List[Dict]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT account_number, bank_code, balance, is_active, 
                       created_at, updated_at
                FROM accounts
                ORDER BY account_number
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_bank_statistics(self, bank_code: str) -> Dict:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as total_accounts,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_accounts,
                       SUM(balance) as total_balance,
                       AVG(balance) as avg_balance,
                       MAX(balance) as max_balance,
                       MIN(balance) as min_balance
                FROM accounts
                WHERE bank_code = ?
            """, (bank_code,))
            
            stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT COUNT(*) as total_transactions
                FROM transactions
                WHERE bank_code = ?
            """, (bank_code,))
            
            stats.update(dict(cursor.fetchone()))
            
            cursor.execute("""
                SELECT COUNT(*) as known_banks,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_banks
                FROM known_banks
            """)
            
            stats.update(dict(cursor.fetchone()))
            
            return stats
            
        finally:
            conn.close()

