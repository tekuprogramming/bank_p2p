import socket
import threading

from db.database import DataBase
from core.protocol import BankProtocol
from core.logger import setup_logging

logger = setup_logging()


class P2PNetwork:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.db = DataBase()
        self.running = False

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()

        self.running = True

        logger.info(f"Server running on {self.host}:{self.port}")

        while self.running:
            client, addr = server.accept()
            threading.Thread(
                target=self.handle_client,
                args=(client, addr),
                daemon=True,
            ).start()

    def handle_client(self, sock, addr):
        ip, _ = addr

        while True:
            data = sock.recv(1024).decode()
            if not data:
                break

            response = self.process_command(data.strip(), ip)
            sock.sendall(response.encode())

        sock.close()

    def process_command(self, data, client_ip):
        protocol = BankProtocol()
        cmd, args = protocol.parse_command(data)

        if cmd not in protocol.COMMANDS:
            return protocol.format_response("", error="Unknown command")

        method = getattr(self, protocol.COMMANDS[cmd])
        return protocol.format_response(cmd, method(*args, client_ip=client_ip))

