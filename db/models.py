from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class BankAccount:
    account_number: int
    bank_code: str
    balance: float = 0.0
    is_active: bool = True
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)
