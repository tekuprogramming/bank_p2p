import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue

from core.utils import current_timestamp, validate_ip_address, validate_port
from network.p2p import P2PNetwork
from core.logger import setup_core_logging  #_core

logger = setup_core_logging()   #_core

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# --- check required keys (reused pattern from LibraryApp) ---
required_keys = ["host", "port"]
missing = [k for k in required_keys if config.get("p2p", k, fallback=None) is None]
if missing:
    logger.warning(f"Missing configuration keys in [p2p]: {', '.join(missing)}")

HOST = config.get("p2p", "host", fallback="0.0.0.0")
PORT = config.getint("p2p", "port", fallback=5000)

class BankMonitorGUI(tk.Tk):
    """
    GUI application for monitoring a P2P bank node.
    Manages node start/stop, displays status, and logs events.
    """
    def __init__(self):
        """
        Initializes the main GUI window, widgets, and state.
        Sets up the message queue, threading, and periodic refreshes.
        """
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

        self.schedule_refresh(self.process_messages, 100)
        self.schedule_refresh(self.update_state, self.update_interval)

    def load_config(self):
        """
        Loads host and port configuration from config file.
        Validates IP address and port using utility functions.
        """
        self.bank_ip = HOST
        self.bank_port = PORT

        if not validate_ip_address(self.bank_ip):
            logger.warning(f"Invalid IP address in config: {self.bank_ip}")
        if not validate_port(self.bank_port):
            logger.warning(f"Invalid port in config: {self.bank_port}")

    def create_widgets(self):
        """
        Creates all GUI widgets:
        - Status labels
        - Event log (scrolled text)
        - Start/Stop buttons
        Organizes layout using frames.
        """
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
        """
        Periodically checks the message queue and displays new messages
        in the log. Scheduled recursively using Tkinter's `after`.
        """
        while not self.message_queue.empty():
            message = self.message_queue.get()
            message_type = message.get("type")
            content = message.get("content")
            timestamp = message.get("timestamp")
            self.add_log(f"{timestamp}: [{message_type}] {content}")

        self.after(100, self.process_messages)

    def add_log(self, message):
        """
        Adds a message to the scrolled text log and logs it
        using the core logger.
        
        Args:
            message (str): The message to log.
        """
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

        logger.info(message)

    def update_state(self):
        """
        Updates the node status label to RUNNING or STOPPED
        based on `is_running` flag. Scheduled recursively.
        """
        if self.is_running:
            self.status_label.config(text="RUNNING", foreground="green")
        else:
            self.status_label.config(text="STOPPED", foreground="red")

        self.after(self.update_interval, self.update_state)

    def start_node(self):
        """
        Starts the P2P node in a separate thread.
        Sets `is_running` to True and posts a start message
        to the message queue.
        """
        if self.is_running:
            return

        self.bank_node = P2PNetwork(self.bank_ip, self.bank_port, monitor_queue=self.message_queue)
        self.server_thread = threading.Thread(target=self.bank_node.start_server, daemon=True)
        self.server_thread.start()

        self.is_running = True
        message = {
            'type': "INFO",
            'content': "Node started",
            'timestamp': current_timestamp()
        }
        self.message_queue.put(message)

    def stop_node(self):
        """
        Stops the P2P node if running.
        Sets `is_running` to False and posts a stop message
        to the message queue.
        """
        if not self.is_running:
            return

        self.bank_node.stop_server()
        self.is_running = False
        message = {
            'type': "INFO",
            'content': "Node stopped",
            'timestamp': current_timestamp()
        }
        self.message_queue.put(message)

    def schedule_refresh(self, func, interval_ms):
        """
        Helper method to call a function repeatedly at a given interval.

        Args:
            func (callable): Function to execute.
            interval_ms (int): Interval in milliseconds between calls.
        """
        func()
        self.after(interval_ms, lambda: self.schedule_refresh(func, interval_ms))


