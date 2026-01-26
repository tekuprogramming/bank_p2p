import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
from datetime import datetime

from network.p2p import P2PNetwork
from core.protocol import BankProtocol
from db.database import DataBase
from core.logger import setup_logging

logger = setup_logging()


class BankMonitorGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("P2P Bank Monitoring")
        self.geometry("1200x800")

        self.message_queue = queue.Queue()

        self.bank_node = None
        self.server_thread = None

        self.is_running = False
        self.update_interval = 2000

        self.load_config()
        self.create_widgets()

        self.after(100, self.process_messages)
        self.after(self.update_interval, self.update_state)