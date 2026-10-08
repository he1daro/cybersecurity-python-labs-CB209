from datetime import timedelta
from getpass import getpass

from task1 import (
    SESSION_TIMEOUT_SEC,
    Admin,
    AuditLog,
    User,
    UserAccount,
)


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
