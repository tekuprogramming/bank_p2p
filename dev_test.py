if __name__ == "__main__":
    print("Testing P2P Bank Core...")
    
    db = Database("test_bank.db")
    print("Database initialized")
    
    bank = P2PBankNode("127.0.0.1", 65530, 5)
    print(f"Bank node created: {bank.bank_code}")
    
    print(f"Bank code: {bank.get_bank_code()}")
    
    try:
        account = bank.create_account("1000.0")
        print(f"Account created: {account}")
    except Exception as e:
        print(f"Error creating account: {e}")
    
    print("Core tests completed")
