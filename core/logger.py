import logging
import configparser
import os
import sys
from datetime import datetime

config = configparser.ConfigParser()
config.read("config.ini")


def setup_core_logging():
    log_level = getattr(logging, config.get("app", "log_level", fallback="INFO"))
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    log_dir = config.get("app", "log_dir", fallback="logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(f"{log_dir}/bank_core_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_core_logging()

