import sqlite3
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter()


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів із фільтрами та пагінацією",
    description=(
        "Повертає список записів, відсортований за зростанням id. "
        "Дозволяє фільтрувати за категорією, статусом, мінімальною оцінкою ризику та пошуком у назві."
    ),
)
def get_records(
    category_id: int | None = Query(
        None, gt=0, description="Фільтр за id категорії (повинен бути > 0)"
    ),
    status_filter: Literal["new", "in_progress", "done"] | None = Query(
        None,
        alias="status",
        description="Фільтр за статусом опрацювання",
    ),
    min_value: float | None = Query(
        None,
        ge=0.0,
        le=10.0,
        description="Фільтр: мінімальна оцінка ризику value >= min_value",
    ),
    q: str | None = Query(
        None,
        min_length=1,
        max_length=120,
        description="Буквальний пошук підрядка в назві title (з урахуванням регістру)",
    ),
    limit: int = Query(
        20, ge=1, le=100, description="Максимальна кількість записів (від 1 до 100)"
    ),
    offset: int = Query(0, ge=0, description="Кількість пропущених записів (>= 0)"),
) -> list[dict[str, Any]]:
    """Отримати список записів."""
    if category_id is not None:
        category = repository.get_category_by_id(category_id)
        if category is None:
            return []

    return repository.get_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів (атомарна транзакція)",
    description=(
        "Приймає JSON-масив об'єктів RecordCreate (від 1 до 100 елементів). "
        "Збереження виконується в межах однієї транзакції: якщо хоча б один елемент некоректний, "
        "містить дублікат code або посилання на неіснуючу категорію, ЖОДЕН запис не зберігається."
    ),
    responses={
        404: {"description": "Одна з категорій не існує"},
        409: {"description": "Дублікат коду в базі або всередині пакета"},
        422: {"description": "Помилка валідації масиву або його елементів"},
    },
)
def bulk_create_records(
    items: Annotated[
        list[RecordCreate],
        Body(
            ...,
            min_length=1,
            max_length=100,
            description="Масив від 1 до 100 записів для додавання",
        ),
    ],
) -> list[dict[str, Any]]:
    """Пакетне додавання записів."""
    codes = [item.code for item in items]
    if len(codes) != len(set(codes)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У наданому пакеті виявлено дублювання коду 'code'.",
        )

    category_ids = {item.category_id for item in items}
    for cat_id in category_ids:
        if repository.get_category_by_id(cat_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Категорію з id={cat_id} не знайдено.",
            )

    records_data = [item.model_dump() for item in items]
    try:
        return repository.bulk_create_records(records_data)
    except sqlite3.IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Помилка цілісності даних при пакетному збереженні (можливо, дублікат 'code' вже існує в базі).",
        ) from err


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати один запис за id",
    description="Повертає один запис разом із category_name.",
    responses={404: {"description": "Запис не знайдено"}},
)
def get_record(
    record_id: int = Path(..., gt=0, description="Додатний ID запису"),
) -> dict[str, Any]:
    """Отримати запис за ID."""
    record = repository.get_record_by_id(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запис з id={record_id} не знайдено.",
        )
    return record


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий запис",
    description="Створює новий запис аудиту контейнерної конфігурації.",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Запис із таким кодом вже існує"},
        422: {"description": "Помилка валідації вхідних даних"},
    },
)
def create_record(payload: RecordCreate) -> dict[str, Any]:
    """Створити один запис."""
    # 1. Перевіряємо існування категорії
    category = repository.get_category_by_id(payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з id={payload.category_id} не знайдено.",
        )

    try:
        return repository.create_record(
            code=payload.code,
            title=payload.title,
            category_id=payload.category_id,
            value=payload.value,
            status=payload.status,
        )
    except sqlite3.IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Запис із кодом '{payload.code}' вже існує.",
        ) from err


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повна заміна змінюваних полів запису",
    description="Повністю замінює всі змінювані поля наявного запису. Передаються всі 5 полів.",
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Дублікат коду запису"},
        422: {"description": "Помилка валідації вхідних даних"},
    },
)
def update_record(
    payload: RecordReplace,
    record_id: int = Path(..., gt=0, description="Додатний ID запису"),
) -> dict[str, Any]:
    """Повною мірою оновити запис."""
    # 1. Перевіряємо існування самого запису
    existing_record = repository.get_record_by_id(record_id)
    if existing_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запис з id={record_id} не знайдено.",
        )

    category = repository.get_category_by_id(payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з id={payload.category_id} не знайдено.",
        )

    try:
        updated_record = repository.update_record(
            record_id=record_id,
            code=payload.code,
            title=payload.title,
            category_id=payload.category_id,
            value=payload.value,
            status=payload.status,
        )
        if updated_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Запис з id={record_id} не знайдено.",
            )
        return updated_record
    except sqlite3.IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Запис із кодом '{payload.code}' вже існує.",
        ) from err


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    description="Видаляє запис за його id.",
    responses={404: {"description": "Запис не знайдено"}},
)
def delete_record(
    record_id: int = Path(..., gt=0, description="Додатний ID запису"),
) -> None:
    """Видалити запис."""
    deleted = repository.delete_record(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запис з id={record_id} не знайдено.",
        )
