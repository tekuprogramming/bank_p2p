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