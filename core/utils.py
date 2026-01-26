def validate_ip_address(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port: int) -> bool:
    return 1024 <= port <= 65535

def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"
