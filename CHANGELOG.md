# Changelog

## 2026-01-15 - Milana Poljanskova
* Nová metoda `setup_logging()` pro nastavení logování
* Datový model `@dataclass` pro reprezentaci bankovního účtu
* Třída `BankAccount` s atributy: `account_number`, `bank_code`, `balance`, `is_active`, `created_at`, `updated_at`
* Metoda `__post_init__` v `BankAccount` pro inicializaci časových razítek
* Metoda `to_dict` v `BankAccount` pro převod objektu na slovník
* Konfigurační soubor `config.ini`

## 2026-01-19 - Milana Poljanskova
* Databázový soubor `bank.db`
* Třída `DataBase`
* Metody třídy `DataBase`: `__init__`, `get_connection`, `init_database`, `execute_query`
* Třída `BankProtocol`

## 2026-01-22 - Milana Poljanskova
* Upraven hlavní soubor (`main`)
* Složka `core` se soubory `logger.py`, `protocol.py` a `__init__.py`
* Složka `db` se soubory `database.py`, `models.py`
* Složka `logs`
* Složka `network` se soubory `p2p.py` a `__init__.py`
* Implementovány metody pro zpracování příkazů

## 2026-01-25 - Hynek Faktor
* Přidány příkazy AR, BN, BA a k nim i příslušné metody - remove_account, bank_amount a get_balance

## 2026-01-25 - Milana Poljanskova
* Import knihovny `sqlite3` pro práci s databází

## 2026-01-26 - Milana Poljanskova
* Přejmenována metoda `setup_logging` na `setup_core_logging` a upravena její implementace
* Upraveny metody `parse_command` a `format_response` ve třídě `BankProtocol`
* Upraveny metody `__init__`, `get_connection` a `init_database` ve třídě `DataBase`
* Upraveny metody `__init__`, `get_local_ip`, `start_server`, `handle_client`, `process_command`, `get_bank_code`, `create_account`, `deposit`, `withdraw` a `proxy_command` ve třídě `P2PNetwork`
* Metody `execute_query`, `get_all_accounts` a `get_bank_statistics` do databázové vrstvy
* Metody `stop_server`, `get_balance`, `get_statistics`, `list_accounts`, `proxy_deposit`, `proxy_withdraw`, `send_gui_message`, `get_gui_messages`, `get_bank_statistics`, `get_all_accounts`, `get_known_banks`, `add_known_banks` a `get_active_connections`
* Soubor `utils.py` s metodami `validate_ip_address`, `validate_port` a `format_currency`
* Testovací soubor `dev_test.py` s testovacími daty
* Složka `gui` se souborem `monitor.py`
* Spouštěcí soubor `gui_main.py`
* Konfigurační informace v `config.ini`

## 2026-01-27 - Hynek Faktor
* oprava importů a metody remove_account

## 2026-01-28 - Milana Poljanskova
* Upravena metoda `handle_client`
* Importována knihovna `ipaddress`
* Přidány importy tříd `DataBase` a `P2PNetwork` a drobné opravy v kódu
* Importována třída `datetime` a přidána metoda `current_timestamp`
* Importovány metody `current_timestamp`, `validate_ip_address` a `validate_port`
* Odstraněny nepoužívané importy
* Upraven konstruktor `__init__`
* Upraveny metody `load_config`, `add_log`, `start_node` a `stop_node`
* Upraveny metody `start_server` a `handle_client`
* Implementován znovupoužitý vzor pro kontrolu konfigurace
* Přidána metoda `schedule_refresh`
* Přidána metoda `send_monitor`

## 2026-01-29 - Milana Poljanskova
* Opravena kontrola rozsahu portů podle zadání
* Přidána dokumentace
* Přidány komentáře do kódu
