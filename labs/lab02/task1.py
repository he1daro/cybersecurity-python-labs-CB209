import hashlib
import hmac
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from getpass import getpass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

PASSWORD_ITERATIONS = 600_000
SALT_LENGTH = VARIANT_NUMBER
SESSION_TIMEOUT_SEC = 900

DOMAIN_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"

EMAIL_PATTERN = rf"^[A-Za-z][A-Za-z0-9_]{{2,63}}@{DOMAIN_LABEL}(?:\.{DOMAIN_LABEL})+$"


class User:
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        active: bool = True,
    ):
        self.username = username
        self.email = email
        self.role = role
        self.active = active
        self.set_password(password)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Email повинен бути рядком.")

        if re.fullmatch(EMAIL_PATTERN, value) is None:
            raise ValueError("Неправильний формат email.")

        self._email = value

    def set_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise ValueError("Пароль повинен бути рядком.")

        salt = os.urandom(SALT_LENGTH)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
        )

        self.__password_salt = salt
        self.__password_hash = password_hash

    def check_password(self, password: str) -> bool:
        if not isinstance(password, str):
            raise ValueError("Пароль повинен бути рядком.")

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PASSWORD_ITERATIONS,
        )

        return hmac.compare_digest(
            self.__password_hash,
            candidate_hash,
        )

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        return (
            f"User(username={self.username}, "
            f"email={self.email}, "
            f"role={self.role}, "
            f"active={self.active})"
        )


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        active: bool = True,
        permissions: set[str] | None = None,
    ):
        super().__init__(
            username=username,
            email=email,
            password=password,
            role="admin",
            active=active,
        )

        self.permissions = set() if permissions is None else set(permissions)

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        permissions_text = ", ".join(sorted(self.permissions))

        if not permissions_text:
            permissions_text = "немає"

        return (
            f"Admin(username={self.username}, "
            f"email={self.email}, "
            f"role={self.role}, "
            f"active={self.active}, "
            f"permissions=[{permissions_text}])"
        )


class Session:
    def __init__(self, ip: str):
        self.ip = ip
        self.login_time = datetime.now(timezone.utc)
        self.last_activity = self.login_time

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if isinstance(timeout_sec, bool) or not isinstance(timeout_sec, int):
            raise TypeError("Таймаут повинен бути цілим числом.")

        if timeout_sec <= 0:
            raise ValueError("Таймаут повинен бути додатним.")

        elapsed = datetime.now(timezone.utc) - self.last_activity
        return elapsed < timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        self.records.append(
            AuditRecord(
                timestamp=datetime.now(timezone.utc),
                username=username,
                action=action,
            )
        )

    def show_all(self) -> None:
        for record in self.records:
            print(
                f"{record.timestamp.isoformat()} | {record.username} | {record.action}"
            )


class UserAccount:
    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ):
        self["user"] = user
        self["session"] = session
        self["audit_log"] = AuditLog() if audit_log is None else audit_log

    def login(self, username: str, password: str, ip: str) -> bool:
        if (
            not self.user.active
            or username != self.user.username
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False

        if not self.user.active or not self.session.is_active(SESSION_TIMEOUT_SEC):
            self.session = None
            return False

        return True

    def logout(self) -> None:
        self.session = None
        self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str):
        if key == "user":
            return self.user

        if key == "session":
            return self.session

        if key == "audit_log":
            return self.audit_log

        raise KeyError(key)

    def __setitem__(self, key: str, value) -> None:
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Очікується об'єкт User або Admin.")

            self.user = value

            self.session = None

        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Очікується об'єкт Session або None.")

            self.session = value

        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Очікується об'єкт AuditLog.")

            self.audit_log = value

        else:
            raise KeyError(key)
        
def demo() -> None:
    print("Створення користувача")

    user = User(
        username="illia",
        email="illia@example.com",
        password=getpass("Задайте пароль користувача: "),
    )

    account = UserAccount(
        user=user,
        audit_log=AuditLog(),
    )

    print(user)

    print("\nУспішний вхід")

    while not account.login(
        username="illia",
        password=getpass("Повторіть пароль користувача: "),
        ip="127.0.0.1",
    ):
        print("Неправильний пароль. Спробуйте ще раз.")

    print("Автентифікований:", account.is_authenticated())

    print("\nНевдалий вхід")

    previous_activity = account["session"].last_activity

    result = account.login(
        username="illia",
        password=getpass("Введіть навмисно неправильний пароль: "),
        ip="127.0.0.1",
    )

    print("Результат входу:", result)
    print(
        "Час останньої активності не змінився:",
        account["session"].last_activity == previous_activity,
    )

    print("\nЗміна email")

    account["user"].email = "illia_new@example.org"
    print("Нова пошта:", account["user"].email)

    try:
        account["user"].email = "1bad@example"
    except ValueError as error:
        print("Помилка:", error)

    print("Пошта після помилки:", account["user"].email)

    print("\nПрава адміністратора")

    admin = Admin(
        username="administrator",
        email="admin@example.com",
        password=getpass("Задайте пароль адміністратора: "),
        permissions={"view_users"},
    )

    admin.grant_permission("edit_users")
    admin.grant_permission("delete_users")

    print(admin)
    print(
        "Може редагувати користувачів:",
        admin.has_permission("edit_users"),
    )

    admin.revoke_permission("edit_users")

    print(
        "Після відкликання дозволу:",
        admin.has_permission("edit_users"),
    )

    print("\nЗавершення сеансу за таймаутом")

    account["session"].last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)

    print("Автентифікований:", account.is_authenticated())
    print("Сеанс:", account["session"])

    print("\nПовторний вхід і вихід")

    while not account.login(
        username="illia",
        password=getpass("Введіть пароль користувача: "),
        ip="127.0.0.1",
    ):
        print("Неправильний пароль. Спробуйте ще раз.")

    print("До виходу:", account.is_authenticated())

    account.logout()

    print("Після виходу:", account.is_authenticated())

    print("\nПеревірка ключів і типів")

    print(account["user"])

    try:
        account["password_hash"]
    except KeyError as error:
        print("Невідомий ключ:", error)

    try:
        account["session"] = "неправильний тип"
    except TypeError as error:
        print("Помилка типу:", error)

    print("\nЖурнал аудиту")
    account["audit_log"].show_all()


if __name__ == "__main__":
    demo()