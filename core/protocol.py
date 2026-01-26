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
        "BN": "bank_number_of_clients",
        "ST": "get_statistics",
        "LB": "list_accounts"
    }

    @staticmethod
    def parse_command(data: str) -> Tuple[str, List[str]]:
        parts = data.strip().split()
        if not parts:
            return '', []
        command = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []
        return command, args

    @staticmethod
    def format_response(command: str, result: Any = None, error: str = None) -> str:
        if error:
            return f"ER {error}\n"
        elif result is not None:
            if isinstance(result, (dict, list)):
                return f"{command} {json.dumps(result, ensure_ascii=False)}\n"
            else:
                return f"{command} {result}\n"
        else:
            return f"{command}\n"

