from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class BankAccount:
    """
    Represents a bank account with account number, bank code, balance, and status.
    Automatically tracks creation and last update timestamps.
    """
    account_number: int
    bank_code: str
    balance: float = 0.0
    is_active: bool = True
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        """
        Initializes timestamps after the dataclass is created.
        Sets `created_at` if not provided and always updates `updated_at` to current time.
        """
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        """
        Converts the BankAccount instance to a dictionary.

        Returns:
            A dictionary representation of the BankAccount.
        """
        return asdict(self)


