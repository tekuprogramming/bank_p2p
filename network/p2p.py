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

    # BC
    def bank_get_code(self, client_ip: str = None):
        return self.get_local_ip()

    # AC
    def create_account(self, client_ip: str = None):
        con = self.db.get_connection()
        try:
            cursor = con.cursor()

            cursor.execute("SELECT max(account_number) FROM accounts")
            max_acc = cursor.fetchone()[0]

            new_account = (max_acc or 10000) + 1

            if new_account > 99999:
                raise ValueError("Bank account limit reached")

            bank_code = self.get_local_ip()

            cursor.execute("""
                INSERT INTO accounts (account_number, bank_code, balance, is_active)
                VALUES (?, ?, 0.0, 1)
            """, (new_account, bank_code))

            con.commit()
            return f"{new_account}/{bank_code}"

        except sqlite3.Error as e:
            con.rollback()
            logger.error(f"Create account error: {e}")
            raise ValueError("Cannot create account")

        finally:
            con.close()

    # AD
    def deposit(self, account_info, amount_str, client_ip=None):

        if "/" not in account_info:
            raise ValueError("Bank account info must contain '/'")

        account_number_str, bank_code = account_info.split("/", 1)

        if bank_code != self.get_local_ip():
            return self.proxy_command("AD", account_info, amount_str, bank_code)

        try:
            account_number = int(account_number_str)
            amount = float(amount_str)

            if amount <= 0:
                raise ValueError()

        except ValueError:
            raise ValueError("Invalid account number or amount")

        con = self.db.get_connection()

        try:
            cursor = con.cursor()

            cursor.execute("""
                SELECT balance, is_active FROM accounts
                WHERE account_number = ? AND bank_code = ?
            """, (account_number, bank_code))

            account = cursor.fetchone()

            if not account:
                raise ValueError("Account not found")

            if not account["is_active"]:
                raise ValueError("Account inactive")

            new_balance = account["balance"] + amount

            cursor.execute("""
                UPDATE accounts
                SET balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_number = ? AND bank_code = ?
            """, (new_balance, account_number, bank_code))

            cursor.execute("""
                INSERT INTO transactions (account_number, bank_code, amount, transaction_type)
                VALUES (?, ?, ?, 'DEPOSIT')
            """, (account_number, bank_code, amount))

            con.commit()

        except sqlite3.Error:
            con.rollback()
            raise ValueError("Transaction failed")

        finally:
            con.close()

    # AW
    def withdraw(self, account_info: str, amount_str: str, client_ip: str = None):

        if "/" not in account_info:
            raise ValueError("Bank account info must contain '/' character")

        account_number_str, bank_code = account_info.split("/", 1)

        if bank_code != self.get_local_ip():
            return self.proxy_command("AW", account_info, amount_str, bank_code)

        try:
            account_number = int(account_number_str)
            amount = float(amount_str)

            if amount <= 0:
                raise ValueError()

        except ValueError:
            raise ValueError("Invalid account number or amount")

        con = self.db.get_connection()

        try:
            cursor = con.cursor()

            cursor.execute("""
                SELECT balance, is_active FROM accounts
                WHERE account_number = ? AND bank_code = ?
            """, (account_number, bank_code))

            account = cursor.fetchone()

            if not account:
                raise ValueError("Account not found")

            if not account["is_active"]:
                raise ValueError("Account inactive")

            if account["balance"] < amount:
                raise ValueError("Insufficient funds")

            new_balance = account["balance"] - amount

            cursor.execute("""
                UPDATE accounts
                SET balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_number = ? AND bank_code = ?
            """, (new_balance, account_number, bank_code))

            cursor.execute("""
                INSERT INTO transactions (account_number, bank_code, amount, transaction_type)
                VALUES (?, ?, ?, 'WITHDRAW')
            """, (account_number, bank_code, amount))

            con.commit()

        except sqlite3.Error as e:
            con.rollback()
            logger.error(f"Withdraw error: {e}")
            raise ValueError("Transaction failed")

        finally:
            con.close()
