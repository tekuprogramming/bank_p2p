from typing import Tuple, List, Any


class BankProtocol:

    COMMANDS = {
        "BC": "bank_get_code",
        "AC": "create_account",
        "AD": "deposit",
        "AW": "withdraw",
        "AB": "get_balance",
        "AR": "remove_account",
        "BA": "bank_amount",
        "BN": "bank_number_of_clients"
    }

    @staticmethod
    def parse_command(data: str) -> Tuple[str, List[str]]:
        parts = data.strip().split()
        return parts[0].upper(), parts[1:]

    @staticmethod
    def format_response(command, result=None, error=None):
        if error:
            return error + "\n"
        if result is None:
            return f"{command}\n"
        return f"{command} {result}\n"
