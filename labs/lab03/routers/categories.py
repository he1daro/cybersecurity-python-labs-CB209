import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Path, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter()


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список усіх категорій",
    description="Повертає список категорій, відсортований за зростанням id.",
)
def get_categories() -> list[dict[str, Any]]:
    """Отримати всі категорії."""
    return repository.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову категорію",
    description="Створює нову категорію з унікальною назвою.",
    responses={
        409: {"description": "Категорія з такою назвою вже існує"},
        422: {"description": "Помилка валідації вхідних даних"},
    },
)
def create_category(payload: CategoryCreate) -> dict[str, Any]:
    """Створити категорію."""
    try:
        return repository.create_category(name=payload.name)
    except sqlite3.IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Категорія з назвою '{payload.name}' вже існує.",
        ) from err


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    description="Видаляє категорію за її id, якщо вона не містить жодного запису.",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Неможливо видалити непорожню категорію"},
    },
)
def delete_category(
    category_id: int = Path(..., gt=0, description="Додатний ID категорії"),
) -> None:
    """Видалити порожню категорію."""
    existing_category = repository.get_category_by_id(category_id)
    if existing_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію з id={category_id} не знайдено.",
        )

    try:
        repository.delete_category(category_id)
    except sqlite3.IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Неможливо видалити категорію з id={category_id}, "
                "оскільки вона містить пов'язані записи."
            ),
        ) from err
