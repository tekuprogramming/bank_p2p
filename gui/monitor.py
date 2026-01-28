import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
from datetime import datetime

from network.p2p import P2PNetwork
from core.protocol import BankProtocol
from db.database import DataBase
from core.logger import setup_core_logging  #_core

logger = setup_core_logging()   #_core

HOST = "0.0.0.0"
PORT = 5000

class BankMonitorGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.stop_btn = None
        self.start_btn = None
        self.log_text = None
        self.ip_label = None
        self.status_label = None
        self.bank_code = None
        self.bank_port = None
        self.bank_ip = None

        self.title("P2P Bank Monitoring")
        self.geometry("1200x800")
        self.config(background="#cccccc")

        self.message_queue = queue.Queue()

        self.bank_node = None
        self.server_thread = None

        self.is_running = False
        self.update_interval = 2000

        self.load_config()
        self.create_widgets()

        self.after(100, self.process_messages)
        self.after(self.update_interval, self.update_state)

    def load_config(self):
        self.bank_ip = HOST
        self.bank_port = PORT

    def create_widgets(self):
        top_frame = ttk.LabelFrame(self, text="Node Status")
        top_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(top_frame, text="STOPPED", foreground="red")
        self.status_label.pack(side="left", padx=10, pady=5)

        self.ip_label = ttk.Label(top_frame, text=f"IP: {self.bank_ip}:{self.bank_port}")
        self.ip_label.pack(side="left", padx=10)

        log_frame = ttk.LabelFrame(self, text="Event Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled", height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ttk.Button(btn_frame, text="Start Node", command=self.start_node)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Node", command=self.stop_node)
        self.stop_btn.pack(side="left", padx=5)

    def process_messages(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            message_type = message.get("type")
            content = message.get("content")
            timestamp = message.get("timestamp")
            self.add_log(f"{timestamp}: [{message_type}] {content}")

        self.after(100, self.process_messages)

    def add_log(self, message):
        self.log_text.configure(state="normal")     #odemkne se
        self.log_text.insert("end", f"{message}\n")
        self.log_text.configure(state="disabled")   #zamkne se
        self.log_text.see("end")    #posune pohled na posledni zpravu

    def update_state(self):
        if self.is_running:
            self.status_label.config(text="RUNNING", foreground="green")
        else:
            self.status_label.config(text="STOPPED", foreground="red")

        self.after(self.update_interval, self.update_state)

    def start_node(self):
        if self.is_running:
            return

        self.bank_node = P2PNetwork(self.bank_ip, self.bank_port, monitor_queue=self.message_queue)
        self.server_thread = threading.Thread(target=self.bank_node.start_server, daemon=True)
        self.server_thread.start()

        self.is_running = True
        message = {
            'type': "INFO",
            'content': "Node started",
            'timestamp': datetime.now().isoformat()
        }
        self.message_queue.put(message)

    def stop_node(self):
        if not self.is_running:
            return

        self.bank_node.stop_server()
        self.is_running = False
        message = {
            'type': "INFO",
            'content': "Node stopped",
            'timestamp': datetime.now().isoformat()
        }
        self.message_queue.put(message)
