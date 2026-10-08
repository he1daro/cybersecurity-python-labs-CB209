# Лабораторна робота №2. 

**Варіант:** 14. Утиліта для консолідації та аналізу логів антивірусного захисту.

# Встановлення залежностей
Проєкт використовує виключно стандартні бібліотеки Python (`json`, `csv`, `argparse`, `logging`, `collections`, `hashlib`, `hmac`, `os`, `re`). 
Додаткові зовнішні пакети встановлювати не потрібно. Для запуску необхідний **Python 3.8 або вище**.

# Структура файлів 
labs/lab02/
├── data/
    └── edr_alerts.json
├── __init__.py
├── edr_summary.csv       # Згенерований звіт
├── main.py               # Демонстрація Завдання 1 
├── README.md             # Цей файл документації
├── system.log            # Файл системних логів
├── task1.py              # Модель користувача й облікового запису (Завдання 1)
└── task2.py              # Утиліта для аналізу логів (Завдання 2)   

Як запускати виконання завдань через Terminal:
1 завдання: python labs\lab02\main.py
2 завдання: python "D:\lpnu\coding\GitHub\cybersecurity-python-labs-CB209\labs\lab02\task2.py" --edr-log "D:\lpnu\coding\GitHub\cybersecurity-python-labs-CB209\labs\lab02\data\edr_alerts.json" --min-severity Low --out-csv "D:\lpnu\coding\GitHub\cybersecurity-python-labs-CB209\labs\lab02\edr_summary.csv" --log-file "D:\lpnu\coding\GitHub\cybersecurity-python-labs-CB209\labs\lab02\system.log"