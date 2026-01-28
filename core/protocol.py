import json
from typing import Tuple, List, Any


class BankProtocol:
    """
    Represents the bank communication protocol.

    Maps short command codes (e.g., "AC") to method names,
    and provides utilities to parse incoming commands and
    format outgoing responses consistently.
    """

    COMMANDS = {
        "BC": "get_bank_code",
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
        """
        Parses an incoming command string.

        Args:
            data: Raw command string received from a client.

        Returns:
            A tuple (command, args) where `command` is the uppercase
            command code and `args` is a list of arguments.
        """
        parts = data.strip().split()
        if not parts:
            return '', []
        command = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []
        return command, args

    @staticmethod
    def format_response(command: str, result: Any = None, error: str = None) -> str:
        """
        Formats a response string to send back to the client.

        Args:
            command: The original command code.
            result: The result of executing the command (optional).
            error: An error message if the command failed (optional).

        Returns:
            A string that follows the bank protocol:
            - Starts with "ER" if there is an error.
            - Includes JSON if the result is a dict or list.
            - Otherwise returns the command and the result.
        """
        if error:
            return f"ER {error}\n"
        elif result is not None:
            if isinstance(result, (dict, list)):
                return f"{command} {json.dumps(result, ensure_ascii=False)}\n"
            else:
                return f"{command} {result}\n"
        else:
            return f"{command}\n"



