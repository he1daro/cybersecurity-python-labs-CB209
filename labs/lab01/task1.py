import random
import string

from rich.console import Console
from rich.table import Table
from rich.text import Text

passwords = [
    "C2@Command",
    "plain123",
    "Backdoor@D3tect",
    "public123",
    "Rootk1t@Hunt",
    "access123",
    "Exploit@An4lysis",
    "basic",
    "Payload@D3code",
    "default123",
]
criteria = {
    "min_length": 10,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}
forbidden_passwords = {
    "plain123",
    "public123",
    "access123",
    "basic",
    "default123",
    "user",
}


def expanding_passwords_list() -> None:
    for i in range(3):
        i = random.randint(0, len(passwords) - 1)
        passwords.append(passwords[i])


def evaluate_password_strength(
    password: str,
    forbidden_passwords: set[str],
    criteria: dict,
    is_unique: bool,
) -> str:
    min_len = criteria.get("min_length")

    if password in forbidden_passwords or len(password) < min_len:
        return "Заборонений"

    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_special = any(char in string.punctuation for char in password)
    has_lower = any(char.islower() for char in password)

    passed_rules = sum(
        [
            has_digit if criteria.get("require_digits", True) else False,
            has_upper if criteria.get("require_upper", True) else False,
            has_special if criteria.get("require_special", True) else False,
        ]
    )

    if passed_rules == 3 and len(password) >= min_len + 4 and is_unique:
        return "Дуже сильний"
    elif passed_rules == 3 and len(password) < min_len + 4:
        return "Сильний"
    elif passed_rules >= 2:
        return "Середній"
    elif has_digit or has_upper or has_special or has_lower:
        return "Слабкий"


def create_table(results: list[tuple[str, str]]) -> Table:
    title = Text("Аналіз надійності паролів", style="bold bright_red")
    table = Table(title=title, header_style="bold bright_green", show_lines=True)
    table.add_column("Пароль", justify="center")
    table.add_column("Надійність/стан", justify="center")

    for password, psw_status in results:
        table.add_row(password, psw_status)

    return table


def analyze_passwords(
    passwords: list[str], forbidden: set[str], criteria: dict
) -> list[tuple[str, str]]:
    analyzed_results = []
    seen = set()

    for pwd in passwords:
        if pwd in seen:
            continue
        seen.add(pwd)

        is_unique = passwords.count(pwd) == 1
        status = evaluate_password_strength(pwd, forbidden, criteria, is_unique)
        analyzed_results.append((pwd, status))

    return analyzed_results


def main():
    expanding_passwords_list()

    results = analyze_passwords(passwords, forbidden_passwords, criteria)
    console = Console()
    table = create_table(results)
    console.print(table, justify="center")


if __name__ == "__main__":
    main()
