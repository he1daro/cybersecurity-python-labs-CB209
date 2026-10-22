from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Контекст життєвого циклу застосунку.

    При запуску сервера перевіряє та створює відсутні таблиці SQLite,
    але НЕ перезаписує наявні дані та НЕ викликає seed автоматично.
    """
    initialize_database()
    yield


app = FastAPI(
    title=config.DOMAIN_NAME,
    description=(
        f"{config.DESCRIPTION}\n\n"
        f"**Одиниця вимірювання (`unit`):** `{config.VALUE_UNIT}` (діапазон 0.0 – 10.0)\n\n"
        f"**Поріг ризику:** `{config.RISK_THRESHOLD}`\n\n"
        "**Категорії:** `image`, `runtime`, `secrets`"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

api_router = APIRouter()
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(records.router, prefix="/records", tags=["Records"])

app.include_router(api_router)


@app.get(
    "/ping",
    summary="Перевірка доступності API",
    description="Повертає статус доступності сервісу.",
    tags=["System"],
)
def ping() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/student",
    summary="Інформація про автора",
    description="Повертає дані студента з shared/student.py.",
    tags=["System"],
)
def get_student_info() -> dict[str, str | int]:
    from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
