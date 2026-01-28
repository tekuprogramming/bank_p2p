from network import p2p
from network.p2p import P2PNetwork
from db.database import DataBase
import unittest

class TestP2PNetwork(unittest.TestCase):

    def setUp(self):
        self.p2p = P2PNetwork(host="127.0.0.1", port=5000)
        self.db = DataBase()

    def test_get_bank_code(self):
        bank_code = self.p2p.get_bank_code()
        self.assertEqual(bank_code, self.p2p.bank_code)

    def test_create_account(self):
        account_info = self.p2p.create_account()
        account_number_str, bank_code = account_info.split('/', 1)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT account_number, bank_code FROM accounts WHERE account_number = ?", (int(account_number_str,),))
        row_account_number_str, row_bank_code = cursor.fetchone()
        conn.close()

        self.assertEqual(account_info, f"{row_account_number_str}/{row_bank_code}")
        with self.assertRaises(ValueError):
            self.p2p.create_account("-1.5")

    def test_deposit(self):
        account_info = self.p2p.create_account()
        account_number_str, bank_code = account_info.split('/', 1)
        self.p2p.deposit(account_info, "20000")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (int(account_number_str, ),))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(float(self.p2p.get_balance(account_info)), float(row[0]))
        self.assertEqual(float(self.p2p.get_balance(account_info)), float(20000))
        with self.assertRaises(ValueError):
            self.p2p.get_balance(f"{account_number_str}.{bank_code}")
            self.p2p.get_balance(f"{0}.{bank_code}")

    def test_withdraw(self):
        account_info = self.p2p.create_account()
        account_number_str, bank_code = account_info.split('/', 1)
        self.p2p.deposit(account_info, "20000")
        self.p2p.withdraw(account_info, "10000")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (int(account_number_str, ),))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(float(self.p2p.get_balance(account_info)), float(row[0]))
        self.assertEqual(float(self.p2p.get_balance(account_info)), float(10000))
        with self.assertRaises(ValueError):
            self.p2p.get_balance(f"{account_number_str}.{bank_code}")
            self.p2p.get_balance(f"{0}.{bank_code}")

    def test_get_balance(self):
        account_info = self.p2p.create_account()
        account_number_str, bank_code = account_info.split('/', 1)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (int(account_number_str, ),))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(float(self.p2p.get_balance(account_info)), float(row[0]))
        with self.assertRaises(ValueError):
            self.p2p.get_balance(f"{account_number_str}.{bank_code}")
            self.p2p.get_balance(f"{0}.{bank_code}")

    def test_bank_amount(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT SUM(balance) FROM accounts""")
        amount = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(self.p2p.bank_amount(), amount)

    def bank_number_of_clients(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT COUNT(*) FROM accounts""")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(self.p2p.bank_number_of_clients(), count)

    def test_remove_account(self):
        account_info = self.p2p.create_account()
        account_number_str, bank_code = account_info.split('/', 1)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT account_number, bank_code FROM accounts WHERE account_number = ?", (int(account_number_str, ),))
        row_account_number_str, row_bank_code = cursor.fetchone()
        conn.close()

        self.assertEqual(account_info, f"{row_account_number_str}/{row_bank_code}")

        self.p2p.remove_account(account_info)
        with self.assertRaises(ValueError):
            self.p2p.remove_account(f"{row_account_number_str}/{row_bank_code}")
            self.p2p.remove_account(f"{row_account_number_str}.{row_bank_code}")
            self.p2p.remove_account(f"{row_account_number_str}.{0}")


if __name__ == "__main__":
    unittest.main()