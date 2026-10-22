import json
import logging
import sqlite3
from pathlib import Path

from labs.lab03.database import get_connection, initialize_database

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
SEED_FILE_PATH = BASE_DIR / "data" / "seed.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def seed_database() -> None:
    """Заповнити базу початковими даними з seed.json в одній транзакції."""
    initialize_database()

    if not SEED_FILE_PATH.exists():
        logger.error(f"Файл початкових даних не знайдено: {SEED_FILE_PATH}")
        return

    try:
        with open(SEED_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as err:
        logger.error(f"Помилка зчитування JSON: {err}")
        return

    categories = data.get("categories", [])
    records = data.get("records", [])

    connection = get_connection()
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]

        if count > 0:
            logger.info("База даних вже містить початкові дані. Пропущено.")
            return

        with connection:
            cursor.executemany(
                "INSERT INTO categories (id, name) VALUES (?, ?)",
                [(cat["id"], cat["name"]) for cat in categories],
            )

            cursor.executemany(
                """
                INSERT INTO records (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        rec["code"],
                        rec["title"],
                        rec["category_id"],
                        rec["value"],
                        rec["status"],
                    )
                    for rec in records
                ],
            )

        logger.info("Базу даних успішно заповнено початковими даними!")

    except sqlite3.IntegrityError as err:
        logger.error(f"Помилка цілісності даних при заповненні бази: {err}")
    except sqlite3.Error as err:
        logger.error(f"Помилка SQLite: {err}")
    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
