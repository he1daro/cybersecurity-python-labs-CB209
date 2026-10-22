from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BASE_CONFIG = ConfigDict(
    str_strip_whitespace=True,
    extra="forbid",
)


class CategoryCreate(BaseModel):
    """Модель для створення нової категорії через POST /categories."""

    model_config = BASE_CONFIG

    name: str = Field(
        ...,
        min_length=2,
        max_length=40,
        description="Унікальна назва категорії (від 2 до 40 символів)",
    )


class CategoryRead(BaseModel):
    """Модель відповіді з даними категорії (GET /categories)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., gt=0, description="Додатний ідентифікатор категорії")
    name: str = Field(..., description="Назва категорії")


class RecordCreate(BaseModel):
    """Модель створення одного запису (оцінка ризику від 0.0 до 10.0)."""

    model_config = BASE_CONFIG

    code: str = Field(
        ...,
        min_length=3,
        max_length=40,
        description="Унікальний код запису (наприклад, V14-01)",
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Назва/опис знахідки аудиту (від 3 до 120 символів)",
    )
    category_id: int = Field(
        ...,
        gt=0,
        description="Ідентифікатор існуючої категорії (додатне ціле число)",
    )
    value: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        allow_inf_nan=False,
        description="Оцінка ризику від 0.0 до 10.0 включно (unit: score)",
    )
    status: Literal["new", "in_progress", "done"] = Field(
        ...,
        description="Стан опрацювання знахідки",
    )


class RecordReplace(RecordCreate):
    """Модель для повного оновлення змінюваних полів запису (PUT /records/{id}).

    Успадковує RecordCreate: усі 5 змінюваних полів є обов'язковими.
    Клієнт НЕ передає id у тілі запиту.
    """


class RecordRead(RecordCreate):
    """Модель відповіді клієнту під час читання запису.

    Включає згенерований базами даних id та назву категорії з JOIN.
    """

    id: int = Field(..., gt=0, description="Додатний ідентифікатор запису")
    category_name: str = Field(
        ..., description="Назва пов'язаної категорії (отримана через JOIN)"
    )


class RecordBulkCreate(BaseModel):
    """Модель для пакетного створення від 1 до 100 записів в одній транзакції."""

    model_config = BASE_CONFIG

    records: list[RecordCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Масив записів для додавання (від 1 до 100 елементів)",
    )
