# Реєстр ризиків контейнерної конфігурації (Лабораторна робота №3, Варіант 14)

Web API для обліку та аудиту результатів перевірки безпеки контейнерного середовища (образів, середовища виконання та секретів).

Предметна область та параметри:
- Одиниця вимірювання (unit): score (оцінка ризику від 0.0 до 10.0)
- Поріг ризику: 6.0
- Категорії: image (id: 1), runtime (id: 2), secrets (id: 3)

## Встановлення залежностей

З кореня репозиторію виконайте:

pip install -r requirements.txt

## Початкове заповнення бази даних

Для створення таблиць та заповнення бази навчальними даними з JSON виконайте:

python -m labs.lab03.seed

## Запуск Web API

Запуск сервера розробки Uvicorn:

python -m uvicorn labs.lab03.main:app --reload

Після запуску документація Swagger UI доступна за адресою: http://127.0.0.1:8000/docs

## Приклади основних запитів

1. Перевірка доступності API:
curl -i "http://127.0.0.1:8000/ping"

2. Отримання списку категорій:
curl -i "http://127.0.0.1:8000/categories"

3. Отримання записів з фільтрацією та пагінацією:
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"

4. Створення нового запису:
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code": "V14-NEW", "title": "Нова знахідка аудиту", "category_id": 1, "value": 7.5, "status": "new"}'

5. Пакетне створення записів (атомарна транзакція):
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code": "V14-B1", "title": "Знахідка 1", "category_id": 1, "value": 5.0, "status": "new"}, {"code": "V14-B2", "title": "Знахідка 2", "category_id": 2, "value": 8.0, "status": "in_progress"}]'