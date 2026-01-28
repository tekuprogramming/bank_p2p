import socket
import sqlite3
import threading
import queue
from datetime import datetime
from typing import Tuple, List, Dict

from db.database import DataBase
from core.protocol import BankProtocol
from core.logger import setup_core_logging

logger = setup_core_logging()


class P2PNetwork:
    """
    Represents a P2P bank network node.
    Handles TCP connections, client commands, and database operations.
    Supports proxying commands to other bank nodes.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 65525, monitor_queue = None, timeout: int = 5):
        """
        Initializes the P2P node with host, port, timeout, and optional monitor queue.
        Sets up the database, protocol handler, and active connections.
        """
        self.host = host
        self.port = port
        self.monitor_queue = monitor_queue
        self.timeout = timeout
        self.is_running = False

        self.db = DataBase()
        self.protocol = BankProtocol()
        self.server_socket = None
        self.active_connections = {}
        
        self.server_thread = None
        
        self.gui_message_queue = monitor_queue
        
        self.bank_code = self.get_local_ip()
        
        logger.info(f"Bank node initialized: {self.bank_code}:{self.port}")

    def get_local_ip(self) -> str:
        """
        Returns the local IP address of the machine.
        Saves the IP as the bank code in config.ini.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            
            import configparser
            config = configparser.ConfigParser()
            config.read("config.ini")
            if "bank" not in config.sections():
                config.add_section("bank")
            config.set("bank", "code", ip)
            with open("config.ini", "w") as f:
                config.write(f)
            
            return ip
        except:
            return '127.0.0.1'

    def start_server(self):
        """
        Starts the TCP server for the bank node.
        Accepts incoming client connections and handles them in separate threads.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1)
            self.is_running = True
            
            logger.info(f"P2P Bank server started on {self.host}:{self.port}")
            self.send_monitor("INFO", f"Server started on {self.host}:{self.port}")
            
            while self.is_running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_socket.settimeout(self.timeout)
                    
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        logger.error(f"Server accept error: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.send_gui_message("ERROR", f"Failed to start server: {e}")
            raise
        finally:
            self.stop_server()

    def stop_server(self):
        """
        Stops the server, closes all active connections, and clears connection data.
        """
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        
        for conn_id, conn_info in list(self.active_connections.items()):
            try:
                conn_info['socket'].close()
            except:
                pass
        
        self.active_connections.clear()
        logger.info("Server stopped")
        self.send_gui_message("INFO", "Server stopped") 

    def handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """
        Handles communication with a connected client.
        Receives commands, processes them, sends responses, and updates connection status.
        """
        client_ip, client_port = address
        connection_id = f"{client_ip}:{client_port}"

        self.active_connections[connection_id] = {
            'socket': client_socket,
            'ip': client_ip,
            'port': client_port,
            'connected_at': datetime.now().isoformat(),
            'status': 'active'
        }

        self.send_monitor("CONNECTION", f"New connection: {connection_id}")
        logger.info(f"New connection from {connection_id}")

        try:
            while self.is_running:

                raw = client_socket.recv(1024)

                if not raw:
                    break

                data = raw.decode("utf-8").strip()

                if data == "":
                    continue

                logger.info(f"Received from {connection_id}: {data}")
                self.send_gui_message("COMMAND", f"{connection_id}: {data}")

                response = self.process_command(data, client_ip)

                client_socket.sendall(response.encode("utf-8"))

                logger.info(f"Sent to {connection_id}: {response.strip()}")
                self.send_gui_message("RESPONSE", f"{connection_id}: {response.strip()}")

                self.active_connections[connection_id]["status"] = "active"

        except socket.timeout:
            logger.warning(f"Connection timeout with {connection_id}")
            self.send_gui_message("WARNING", f"Timeout: {connection_id}")

        except Exception as e:
            logger.error(f"Error handling client {connection_id}: {e}")
            self.send_gui_message("ERROR", f"Client error {connection_id}: {e}")

        finally:
            client_socket.close()

            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

            logger.info(f"Connection closed: {connection_id}")
            self.send_gui_message("CONNECTION", f"Closed: {connection_id}")

    def process_command(self, command_str: str, client_ip: str = None) -> str:
        """
        Parses and executes a command received from a client.
        Returns the formatted response string.
        """
        command, args = self.protocol.parse_command(command_str)
        
        if command not in self.protocol.COMMANDS:
            return self.protocol.format_response('', error="Unknown command")
        
        handler_name = self.protocol.COMMANDS[command]
        handler = getattr(self, handler_name, None)
        
        if not handler:
            return self.protocol.format_response('', error="Command not implemented")
        
        try:
            result = handler(*args, client_ip=client_ip)
            return self.protocol.format_response(command, result)
        except ValueError as e:
            return self.protocol.format_response('', error=str(e))
        except Exception as e:
            logger.error(f"Command {command} error: {e}")
            return self.protocol.format_response('', error="Command incomplete")

    # BC
    def get_bank_code(self, client_ip: str = None) -> str:
        """
        Gets bank code
        :return: IP of the bank
        """
        return self.bank_code

    # AC
    def create_account(self, initial_balance: str = "0.0", client_ip: str = None) -> str:
        """
        Creates an account with given initial balance
        :param initial_balance: Account principal amount
        :param client_ip: IP of the client
        :return: Number of created account
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT MAX(account_number) FROM accounts")
            max_acc = cursor.fetchone()[0]
            new_account = (max_acc or 10000) + 1
            
            if new_account > 99999:
                self.send_gui_message("ERROR", "Bank account limit reached")
                logger.info("ER Bank account limit reached")
                raise ValueError("ER Bank account limit reached")
            
            try:
                balance = float(initial_balance) if initial_balance else 0.0
                if balance < 0:
                    self.send_gui_message("ERROR", "Initial balance cannot be negative")
                    logger.info("ER Initial balance cannot be negative")
                    raise ValueError("ER Initial balance cannot be negative")
            except ValueError:
                self.send_gui_message("ERROR", "Invalid initial balance")
                logger.info("ER Invalid initial balance")
                raise ValueError("ER Invalid initial balance")
            
            cursor.execute("""
                INSERT INTO accounts (account_number, bank_code, balance, is_active)
                VALUES (?, ?, ?, 1)
            """, (new_account, self.bank_code, balance))
            
            if balance > 0:
                cursor.execute("""
                    INSERT INTO transactions 
                    (account_number, bank_code, amount, transaction_type, description)
                    VALUES (?, ?, ?, 'INITIAL_DEPOSIT', 'Initial deposit')
                """, (new_account, self.bank_code, balance))
            
            conn.commit()
            
            account_info = f"{new_account}/{self.bank_code}"

            logger.info(f"Account created: {account_info} with balance ${balance:,.2f}")
            self.send_gui_message("ACCOUNT", f"Created: {account_info}")
            
            return account_info
            
        except sqlite3.Error as e:
            conn.rollback()

            logger.error(f"Create account error: {e}")
            raise ValueError("Cannot create account")
        finally:
            conn.close()

    # AD
    def deposit(self, account_info: str, amount_str: str, client_ip: str = None) -> None:
        """
        Deposits an amount into the account
        :param account_info: String in format number/bank code
        :param amount_str: Amount to be deposited into the account
        :param client_ip: IP of the client
        :return: If the user enters a different bank, it calls the method proxy_command
        """
        if '/' not in account_info:
            self.send_gui_message("ERROR", "Invalid account format. Use: account_number/bank_code")
            logger.error("ER Invalid account format. Use: account_number/bank_code")
            raise ValueError("ER Invalid account format. Use: account_number/bank_code")
        
        account_number_str, bank_code = account_info.split('/', 1)
        
        if bank_code != self.bank_code:
            return self.proxy_command('AD', account_info, amount_str, bank_code)
        
        try:
            account_number = int(account_number_str)
            amount = float(amount_str)
            
            if amount <= 0:
                self.send_gui_message("ERROR", "Amount must be positive")
                logger.error("ER Amount must be positive")
                raise ValueError("ER Amount must be positive")
            if amount > 1000000:
                self.send_gui_message("ERROR", "Maximum deposit amount is $1,000,000")
                logger.error("ER Maximum deposit amount is $1,000,000")
                raise ValueError("ER Maximum deposit amount is $1,000,000")
        except ValueError:
            self.send_gui_message("ER", "Invalid account number or amount format")
            logger.error("ER Invalid account number or amount format")
            raise ValueError("ER Invalid account number or amount format")
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT balance, is_active FROM accounts 
                WHERE account_number = ? AND bank_code = ?
            """, (account_number, bank_code))
            
            account = cursor.fetchone()
            if not account:
                self.send_gui_message("ERROR", "Account not found")
                logger.error("ER Account not found")
                raise ValueError("ER Account not found")
            if not account['is_active']:
                self.send_gui_message("ERROR", "Account is not active")
                logger.error("ER Account is not active")
                raise ValueError("ER Account is not active")
            
            new_balance = account['balance'] + amount
            cursor.execute("""
                UPDATE accounts 
                SET balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_number = ? AND bank_code = ?
            """, (new_balance, account_number, bank_code))
            
            cursor.execute("""
                INSERT INTO transactions (account_number, bank_code, amount, transaction_type, description)
                VALUES (?, ?, ?, 'DEPOSIT', 'Deposit from network')
            """, (account_number, bank_code, amount))
            
            conn.commit()
            
            logger.info(f"Deposited ${amount:,.2f} to account {account_info}")
            self.send_gui_message("TRANSACTION", f"Deposit: {account_info} +${amount:,.2f}")
            
        except sqlite3.Error as e:
            conn.rollback()
            self.send_gui_message("ERROR", "Deposit error")
            logger.error(f"Deposit error: {e}")
            raise ValueError("Transaction failed")
        finally:
            conn.close()

    # AW
    def withdraw(self, account_info: str, amount_str: str, client_ip: str = None) -> None:
        """
        Withdraws an amount from the account
        :param account_info: String in format number/bank code
        :param amount_str: Amount to withdraw from the account
        :param client_ip: IP of the client
        :return: If the user enters a different bank, it calls the method proxy_command
        """
        if '/' not in account_info:
            self.send_gui_message("ERROR", "Invalid account format. Use: account_number/bank_code")
            logger.error("ER Invalid account format. Use: account_number/bank_code")
            raise ValueError("ER Invalid account format. Use: account_number/bank_code")
        
        account_number_str, bank_code = account_info.split('/', 1)
        
        if bank_code != self.bank_code:
            return self.proxy_command('AW', account_info, amount_str, bank_code)
        
        try:
            account_number = int(account_number_str)
            amount = float(amount_str)
            
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount > 1000000:
                raise ValueError("Maximum withdrawal amount is $1,000,000")
        except ValueError:
            raise ValueError("Invalid account number or amount format")
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT balance, is_active FROM accounts 
                WHERE account_number = ? AND bank_code = ?
            """, (account_number, bank_code))
            
            account = cursor.fetchone()
            if not account:
                raise ValueError("Account not found")
            if not account['is_active']:
                raise ValueError("Account is not active")
            
            if account['balance'] < amount:
                raise ValueError("Insufficient funds")
            
            new_balance = account['balance'] - amount
            cursor.execute("""
                UPDATE accounts 
                SET balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_number = ? AND bank_code = ?
            """, (new_balance, account_number, bank_code))
        
            cursor.execute("""
                INSERT INTO transactions (account_number, bank_code, amount, transaction_type, description)
                VALUES (?, ?, ?, 'WITHDRAWAL', 'Withdrawal from network')
            """, (account_number, bank_code, amount))
            
            conn.commit()
            
            logger.info(f"Withdrew ${amount:,.2f} from account {account_info}")
            self.send_gui_message("TRANSACTION", f"Withdrawal: {account_info} -${amount:,.2f}")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Withdraw error: {e}")
            raise ValueError("Transaction failed")
        finally:
            conn.close()
    # AB
    def get_balance(self, account_info: str, client_ip: str = None) -> str:
        """
        Gets the balance of the account
        :param account_info: String in format number/bank code
        :param client_ip: IP of the client
        :return: returns the balance of the account
        """
        if '/' not in account_info:
            self.send_gui_message("ERROR", "Invalid account format. Use: account_number/bank_code")
            logger.error("ER Invalid account format. Use: account_number/bank_code")
            raise ValueError("ER Invalid account format. Use: account_number/bank_code")
        
        account_number_str, bank_code = account_info.split('/', 1)
        
        if bank_code != self.bank_code:
            return self.proxy_command('AB', account_info, None, bank_code)
        
        try:
            account_number = int(account_number_str)
        except ValueError:
            self.send_gui_message("ERROR", "Invalid account number")
            logger.error("ER Invalid account number")
            raise ValueError("ER Invalid account number")
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT balance FROM accounts 
                WHERE account_number = ? AND bank_code = ? AND is_active = 1
            """, (account_number, bank_code))
            
            account = cursor.fetchone()
            if not account:
                self.send_gui_message("ERROR", "Account not found or inactive")
                logger.error("ER Account not found or inactive")
                raise ValueError("ER Account not found or inactive")
            
            return str(account['balance'])
            
        except sqlite3.Error as e:
            self.send_gui_message("ERROR", "Get balance error")
            logger.error(f"ER Get balance error: {e}")
            raise ValueError("ER Database query failed")
        finally:
            conn.close()

    def bank_amount(self, client_ip: str = None):
        """
        gets amount of a bank accounts
        :param client_ip: IP of the client
        :return: amount of the bank accounts
        """
        con = self.db.get_connection()

        try:
            cursor = con.cursor()
            cursor.execute("""SELECT SUM(balance) FROM accounts""")
            amount = cursor.fetchone()[0]
            if amount is None:
                amount = 0
            return amount

        except sqlite3.Error as e:
            self.send_gui_message("ERROR", "Bank amount query error")
            logger.error(f"ER Bank amount query error: {e}")
            raise ValueError("ER Database query failed")

        finally:
            con.close()

    def bank_number_of_clients(self, client_ip: str = None):
        """
        gets the number of bank accounts
        :param client_ip: IP of the client
        :return: count of accounts in the bank
        """
        con = self.db.get_connection()
        try:
            cursor = con.cursor()
            cursor.execute("""SELECT COUNT(*) FROM accounts""")
            count = cursor.fetchone()[0]
            return count

        except sqlite3.Error as e:
            self.send_gui_message("ERROR", "Bank number query error")
            logger.error(f"ER Bank number query error: {e}")
            raise ValueError("ER Database query failed")

        finally:
            con.close()

    def remove_account(self, account_info: str, client_ip: str = None):
        """
        Removes an account from the bank
        :param account_info: string in format number/bank code
        :param client_ip: IP of the client
        :return: result of the operation
        """
        if "/" not in account_info:
            self.send_gui_message("ERROR", "Bank account info must contain '/' character")
            logger.error("ER Bank account info must contain '/' character")
            raise ValueError("ER Bank account info must contain '/' character")

        account_number_str, bank_code = account_info.split("/", 1)

        if bank_code != self.get_local_ip():
            #return self.proxy_command('AR', account_info, None, bank_code)
            self.send_gui_message("ERROR", "Invalid bank code")
            logger.debug("ER Invalid bank code")
            raise ValueError("ER Invalid bank code")

        con = self.db.get_connection()

        try:
            cursor = con.cursor()
            account_number = int(account_number_str)

            cursor.execute(""" SELECT balance FROM accounts WHERE account_number = ? AND bank_code = ? """, (account_number, bank_code))
            row = cursor.fetchone()
            if row is None:
                self.send_gui_message("ERROR", "Account not found")
                logger.debug("ER Account not found")
                raise ValueError("ER Account not found")

            balance = row[0]
            if balance is None:
                balance = 0

            if balance > 0:
                self.send_gui_message("ERROR", "ER Cannot delete bank account containing founds")
                logger.debug("ER Cannot delete bank account containing founds")
                raise Exception("ER Cannot delete bank account containing founds")

            cursor.execute("""
                DELETE from accounts
                WHERE account_number = ? AND bank_code = ?
                """, (account_number, bank_code))

            con.commit()
            self.send_gui_message("INFO", f"Account removed successfully")

        except sqlite3.Error as e:
            con.rollback()
            logger.error(f"ER Account remove failed: {e}")
            self.send_gui_message("ERROR", "ER Account remove failed")
            raise ValueError("ER Database query failed")

        finally:
            con.close()

    def get_statistics(self, client_ip: str = None) -> Dict:
      """Returns statistics about the bank, including active connections and bank code."""
        stats = self.db.get_bank_statistics(self.bank_code)
        
        stats['active_connections'] = len(self.active_connections)
        stats['bank_code'] = self.bank_code
        stats['port'] = self.port
        stats['is_running'] = self.is_running
        
        return stats
    
    def list_accounts(self, client_ip: str = None) -> List[Dict]:
        """Returns a list of all accounts in the bank."""
        return self.db.get_all_accounts()
    
    def proxy_command(self, command: str, account_info: str, amount: str = None, target_bank: str = None) -> str:
        """
        Forwards a command to another bank node.
        Handles TCP connection and returns the response.
        """
        try:
            if ':' in target_bank:
                bank_ip, bank_port_str = target_bank.split(':', 1)
                bank_port = int(bank_port_str)
            else:
                bank_ip = target_bank
                bank_port = 65525
            
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.settimeout(self.timeout)
            
            proxy_socket.connect((bank_ip, bank_port))
            
            if amount:
                cmd_data = f"{command} {account_info} {amount}\n"
            else:
                cmd_data = f"{command} {account_info}\n"
            
            proxy_socket.sendall(cmd_data.encode('utf-8'))
            
            response = proxy_socket.recv(1024).decode('utf-8').strip()
            
            proxy_socket.close()
            
            self.add_known_bank(target_bank, bank_ip, bank_port)
            
            logger.info(f"Proxied {command} to {target_bank}: {response}")
            self.send_gui_message("PROXY", f"{command} to {target_bank}")
            
            return response
            
        except socket.error as e:
            logger.error(f"Proxy error to {target_bank}: {e}")
            raise ValueError(f"Cannot connect to bank {target_bank}")
        except Exception as e:
            logger.error(f"Proxy command error: {e}")
            raise ValueError("Proxy operation failed")

    def proxy_deposit(self, account_info: str, amount: float) -> str:
        """Proxies a deposit command to another bank node."""
        account_number_str, bank_code = account_info.split('/', 1)
        return self.proxy_command('AD', account_info, str(amount), bank_code)
    
    def proxy_withdraw(self, account_info: str, amount: float) -> str:
        """Proxies a withdrawal command to another bank node."""
        account_number_str, bank_code = account_info.split('/', 1)
        return self.proxy_command('AW', account_info, str(amount), bank_code)

    def send_gui_message(self, message_type: str, content: str):
        """Sends a structured message to the GUI message queue."""
        try:
            message = {
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            self.gui_message_queue.put(message)
        except:
            pass
    
    def get_gui_messages(self) -> List[Dict]:
        """Returns all pending messages from the GUI queue."""
        messages = []
        while not self.gui_message_queue.empty():
            try:
                messages.append(self.gui_message_queue.get_nowait())
            except:
                break
        return messages
    
    def get_bank_statistics(self) -> Dict:
        """Returns statistics about the bank, including active connections and status."""
        stats = self.db.get_bank_statistics(self.bank_code)
        stats['bank_code'] = self.bank_code
        stats['active_connections'] = len(self.active_connections)
        stats['is_running'] = self.is_running
        return stats
    
    def get_all_accounts(self) -> List[Dict]:
        """Returns all accounts stored in the database."""
        return self.db.get_all_accounts()
    
    def get_known_banks(self) -> List[Dict]:
        """Returns the list of known banks and their connection info."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bank_code, ip_address, port, last_seen, is_active
                FROM known_banks
                ORDER BY last_seen DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def add_known_bank(self, bank_code: str, ip_address: str, port: int):
        """Adds or updates a known bank in the database."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO known_banks
                (bank_code, ip_address, port, last_seen, is_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
            """, (bank_code, ip_address, port))
            conn.commit()
        finally:
            conn.close()
    
    def get_active_connections(self) -> List[Dict]:
        """Returns a list of all currently active client connections."""
        connections = []
        for conn_id, conn_info in self.active_connections.items():
            connections.append({
                'id': conn_id,
                'ip': conn_info['ip'],
                'port': conn_info['port'],
                'connected_at': conn_info['connected_at'],
                'status': conn_info['status']
            })
        return connections

    def send_monitor(self, msg_type, content):
        """Sends a message to the monitor queue for GUI display or logging."""
        if self.monitor_queue:
            self.monitor_queue.put({
                "type": msg_type,
                "content": content,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

