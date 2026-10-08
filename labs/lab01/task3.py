import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from functools import wraps

from rich.console import Console
from rich.table import Table

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

MIN_LENGTH = 16
salt = str(VARIANT_NUMBER).zfill(5)


class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = salt) -> str:
    if password is None or password == "" or salt is None or salt == "":
        raise ValueError("Пароль та сіль не можуть бути порожними!")
    elif len(password) < MIN_LENGTH:
        raise ValidationError("Пароль коротший за мінімальну довжину (16 символів)!")

    combined_psw = password + salt
    generated_hash = hashlib.sha512(combined_psw.encode()).hexdigest()
    return generated_hash


def create_user(username: str, password: str) -> tuple[str, str]:
    hash_value = generate_hash(password, salt=salt)
    return (username, hash_value)


def create_users(users_list: list, file_path: str) -> None:
    file_path = os.path.join("labs", "lab01", "data", "users.csv")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for username, password in users_list:
                user_entry = create_user(username, password)
                writer.writerow(user_entry)
    except FileNotFoundError:
        print("Помилка! Файл не знайдено.")
    except PermissionError:
        print("Помилка! Немає доступу до файлу.")
    except OSError as e:
        print(f"Помилка файлової системи при записі: {e}")


users_db = []


def load_users(file_path: str) -> list[tuple[str, str]]:
    users_db = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    users_db.append((row[0], row[1]))
    except FileNotFoundError:
        print("Помилка! Файл не знайдено.")
    except PermissionError:
        print("Помилка! Немає доступу до файлу.")
    except OSError as e:
        print(f"Помилка файлової системи при записі: {e}")
    return users_db


def display_users_table(users_db: list[tuple[str, str]]) -> None:
    console = Console()
    table = Table(
        title="База даних зареєстрованих користувачів",
        header_style="bold bright_cyan",
        show_lines=True,
    )

    table.add_column("Логін", justify="center", style="bold yellow")
    table.add_column("Хеш пароля", justify="center", style="green")

    for username, pwd_hash in users_db:
        table.add_row(username, pwd_hash)

    console.print(table)


def log_event(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if len(args) > 0 else kwargs.get("username", "unknown")
        res = func(*args, **kwargs)
        result_status = "success" if res else "failure"

        log_data = {
            "event": "login",
            "user": str(username),
            "result": result_status,
            "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "args": list(args),
            "kwargs": kwargs,
        }

        log_path = os.path.join("labs", "lab01", "data", "log.json")
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            logs = []
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                try:
                    with open(log_path, mode="r", encoding="utf-8") as f:
                        logs = json.load(f)
                        if not isinstance(logs, list):
                            logs = [logs]
                except json.JSONDecodeError:
                    logs = []

            logs.append(log_data)

            with open(log_path, mode="w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except FileNotFoundError:
            print("Помилка! Файл не знайдено.")
        except PermissionError:
            print("Помилка! Немає доступу до файлу.")
        except OSError as e:
            print(f"Помилка файлової системи при записі: {e}")

        return res

    return wrapper


@log_event
def login(username: str, password: str) -> bool:
    try:
        if password is None or password == "" or username is None or username == "":
            raise ValueError("Пароль та логін не можуть бути порожними!")

        input_hash = generate_hash(password, salt=salt)
        for user, psw in users_db:
            if username == user:
                return input_hash == psw

        return False

    except (ValueError, ValidationError) as e:
        print(f"Помилка входу ({type(e).__name__}): {e}")
        return False


def main():
    global users_db
    csv_file_path = os.path.join("labs", "lab01", "data", "users.csv")

    users_to_register = (
        ("sec_admin", "AdminSec#2026!SecureKey"),
        ("crypto_analyst", "Tr4d1ng#Alg0_Pr0t0c0l"),
        ("smart_auditor", "Audit$C0ntracts#V3rify"),
        ("node_operator", "V4l1dat0r*N0de#99Key"),
        ("defi_dev", "D3f1!Pr0t0c0l$M4st3r"),
        ("net_sentinel", "G4t3w4y#P4ck3t$Tr4c3"),
        ("soc_analyst", "Inc1d3nt#R3sp0ns3!2026"),
        ("pentester", "Expl01t#Hunt3r$Root9"),
        ("cloud_guard", "Cl0ud#P0l1cy$Gu4rd14n"),
        ("key_manager", "K3ySt0r3#Pr1v4t3!Acc3ss"),
    )

    create_users(users_to_register, csv_file_path)

    users_db = load_users(csv_file_path)

    if users_db:
        display_users_table(users_db)
    for i in users_to_register:
        print(f"Вхід: user = '{i[0]}', status = {login(i[0], i[1])}")


if __name__ == "__main__":
    main()
