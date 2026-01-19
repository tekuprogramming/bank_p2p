import socket
import threading
import sqlite3
import json
import logging
import configparser
import time
import sys
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import hashlib
import ipaddress

# repeating use of code
config = configparser.ConfigParser()
config.read('config.ini')

def setup_logging():
    log_level = getattr(logging, config.get('app', 'log_level', fallback='INFO'))
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # creating a directory for logs if it doesn't exist
    log_dir = config.get("app", "log_dir", fallback="logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.FileHandler(f"{log_dir}/bank_{datetime.now().strftime('%Y%m%d')}.log"), logging.StreamHandler(sys.stdout)])

    return logging.getLogger(__name__)

logger = setup_logging()

# data models
@dataclass # from dataclasses
class BankAccount:
    account_number: int
    bank_code: str
    balance: float = 0.0
    is_active: bool = True
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):

        return asdict(self)

class DataBase: # class for working with SQLite database (repeating use of code)
    def __init__(self, db_path: str = "bank.db"):
        self.db_path = db_path

    def get_connection(self): # connection with database (similar to method getcon in previous project)
        try:
            con = sqlite3.connect(self.db_path)
            con.row_factory = sqlite3.Row
            return con
        except sqlite3.Error as e:
            logger.error(e)
            raise

    def init_database(self):
        con = self.get_connection()
        try:
            cursor = con.cursor()
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
                    is_active INTEGER DEFAULT 1
                )
            """)
            con.commit()
            logger.info("Database initialized")
        except sqlite3.Error as e:
            logger.error(e)
            raise
        finally:
            con.close()

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        try:
            con = self.get_connection()
            cursor = con.cursor()
            cursor.execute(query, params or ())
            if fetch:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid
            con.commit()
            return result
        except sqlite3.Error as e:
            con.rollback()
            logger.error(e)
            raise
        finally:
            con.close()

class BankProtocol: # connection protocol
   COMMANDS = {"BC": "get_bank_code", "AC": "create_account", "AD": "deposit", "AW": "withdraw", "AB": "get_balance", "AR": "remove_account", "BA": "get_total_balance", "BN": "get_customer_count"}
