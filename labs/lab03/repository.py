import sqlite3
from typing import Any

from labs.lab03.database import get_connection


def get_category_by_id(category_id: int) -> dict[str, Any] | None:
    """Отримати категорію за її id."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def create_category(name: str) -> dict[str, Any]:
    """Створити нову категорію."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            category_id = cursor.lastrowid

        category = get_category_by_id(category_id)
        if category is None:
            raise sqlite3.OperationalError("Не вдалося створити категорію.")
        return category
    finally:
        connection.close()


def get_categories() -> list[dict[str, Any]]:
    """Отримати список усіх категорій, відсортований за зростанням id."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def delete_category(category_id: int) -> bool:
    """Видалити порожню категорію за її id.

    Якщо категорія містить записи, виникне sqlite3.IntegrityError через
    ON DELETE RESTRICT.
    """
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            if cursor.rowcount == 0:
                return False
        return True
    finally:
        connection.close()


def create_record(
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict[str, Any]:
    """Створити один новий запис."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO records (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (code, title, category_id, value, status),
            )
            record_id = cursor.lastrowid

        record = get_record_by_id(record_id)
        if record is None:
            raise sqlite3.OperationalError("Не вдалося створити запис.")
        return record
    finally:
        connection.close()


def get_record_by_id(record_id: int) -> dict[str, Any] | None:
    """Отримати один запис за id разом із category_name через JOIN."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
                   r.value, r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати список записів із фільтрацією, сортуванням."""
    query = """
        SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
               r.value, r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
    """
    conditions: list[str] = []
    params: list[Any] = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)

    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)

    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)

    if q is not None and q != "":
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def update_record(
    record_id: int,
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict[str, Any] | None:
    """Повне оновлення змінюваних полів запису.

    Якщо запису з таким id немає, повертає None.
    """
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE records
                SET code = ?, title = ?, category_id = ?, value = ?, status = ?
                WHERE id = ?
                """,
                (code, title, category_id, value, status, record_id),
            )
            if cursor.rowcount == 0:
                return None

        return get_record_by_id(record_id)
    finally:
        connection.close()


def delete_record(record_id: int) -> bool:
    """Видалення запису по id.

    Якщо запису з таким id немає, повертає False.
    """
    connection = get_connection()
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            if cursor.rowcount == 0:
                return False
        return True
    finally:
        connection.close()


def bulk_create_records(
    records_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Пакетне створення записів в межах ОДНІЄЇ транзакції.

    Якщо хоча б один елемент некоректний або створює дублікат,
    весь пакет скасовується.
    """

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    created_ids: list[int] = []

    try:
        with connection:
            cursor = connection.cursor()
            for item in records_data:
                cursor.execute(
                    """
                    INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item["code"],
                        item["title"],
                        item["category_id"],
                        item["value"],
                        item["status"],
                    ),
                )
                if cursor.lastrowid is not None:
                    created_ids.append(cursor.lastrowid)

        if not created_ids:
            return []

        placeholders = ",".join("?" for _ in created_ids)
        query = f"""
            SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
                   r.value, r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE r.id IN ({placeholders})
            ORDER BY r.id ASC
        """
        cursor = connection.cursor()
        cursor.execute(query, created_ids)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
