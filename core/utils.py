import ipaddress
from datetime import datetime

def current_timestamp() -> str:
    """
    Returns the current time as a string in HH:MM:SS format.

    Useful for logging or displaying timestamps in the GUI.
    """
    return datetime.now().strftime("%H:%M:%S")

def validate_ip_address(ip: str) -> bool:
    """
    Validates whether the given string is a proper IPv4 or IPv6 address.

    Args:
        ip: The IP address string to validate.

    Returns:
        True if the IP address is valid, False otherwise.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port: int) -> bool:
    """
    Validates whether the given port number is within the valid range.

    Args:
        port: The port number to validate.

    Returns:
        True if the port is between 1024 and 65535 (inclusive), False otherwise.
    """
    return 1024 <= port <= 65535

def format_currency(amount: float) -> str:
    """
    Formats a numeric value as a currency string in USD format.

    Args:
        amount: The numeric amount to format.

    Returns:
        A string with a dollar sign and two decimal places, e.g., "$1,234.56".
    """
    return f"${amount:,.2f}"

