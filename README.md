# Enhanced Mock Server v2.0 - Standalone Project

Отдельный проект мок-сервера для использования в多个 учебных модулях.

## 📁 Структура проекта

```
MockServer_Standalone/
├── mock_server.py          # Основной сервер
├── data_store.py           # Хранилище данных
├── validators.py           # Валидация
├── requirements.txt        # Зависимости
├── start.sh               # Запуск (macOS/Linux)
├── start.bat              # Запуск (Windows)
├── .gitignore
├── README.md
└── data/                   # Данные сервера
    ├── entities.json
    └── request_history.json
```

## 🚀 Быстрый старт

### 1. Открыть проект в PyCharm

```
File → Open → Выбрать папку MockServer_Standalone
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

Или в PyCharm:
```
Settings → Project → Python Interpreter → + → Install packages
```

### 3. Запустить сервер

**В терминале PyCharm:**
```bash
python mock_server.py
```

Или использовать скрипт:
```bash
./start.sh        # macOS/Linux
start.bat         # Windows
```

### 4. Проверить работу

Откройте: http://127.0.0.1:8000/docs

---

## 🔗 Использование из других проектов

Сервер работает на `http://127.0.0.1:8000` и доступен для всех проектов на компьютере.

### Пример использования в тестах:

```python
import requests

MOCK_SERVER_URL = "http://127.0.0.1:8000"

def test_create_entity():
    response = requests.post(
        f"{MOCK_SERVER_URL}/entities",
        json={"name": "Test"}
    )
    assert response.status_code == 201
```

---

## 💡 Преимущества отдельного проекта

✅ **Один сервер для всех модулей** - не нужно копировать  
✅ **Независимое управление** - можно обновлять отдельно  
✅ **Чистая архитектура** - разделение ответственности  
✅ **Легко запустить** - один раз запустил, используешь везде  

---

## 📖 API Documentation

Swagger UI доступен по адресу: http://127.0.0.1:8000/docs

---

## 🏨 API для работы с бронированиями

Сервер поддерживает полный CRUD для управления бронированиями.

### Модели данных:

**BookingDates:**
```json
{
  "checkin": "2026-08-06",
  "checkout": "2026-08-10"
}
```

**BookingCreate:**
```json
{
  "firstname": "Artem",
  "lastname": "Altynov",
  "totalprice": 15000,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2026-08-06",
    "checkout": "2026-08-10"
  },
  "additionalneeds": "Breakfast"
}
```

### Эндпоинты:

**POST /booking** - Создание бронирования
```python
import requests

booking_data = {
    "firstname": "Artem",
    "lastname": "Altynov",
    "totalprice": 15000,
    "depositpaid": True,
    "bookingdates": {
        "checkin": "2026-08-06",
        "checkout": "2026-08-10"
    },
    "additionalneeds": "Breakfast"
}

response = requests.post(
    "http://127.0.0.1:8000/booking",
    json=booking_data
)

# Ответ:
# {
#   "bookingid": 1,
#   "booking": {...данные бронирования...}
# }
```

**GET /booking/{booking_id}** - Получение бронирования по ID
```python
response = requests.get("http://127.0.0.1:8000/booking/1")

# Ответ: данные бронирования
# Если не найдено: 404 Not Found
```

**DELETE /booking/{booking_id}** - Удаление бронирования
```python
response = requests.delete("http://127.0.0.1:8000/booking/1")

# Ответ: {"message": "Booking 1 deleted successfully"}
```

### Важные особенности:

- ✅ `bookingid` генерируется автоматически (начинается с 1)
- ✅ Данные хранятся в памяти (очищаются при перезапуске сервера)
- ✅ Валидация всех обязательных полей через Pydantic
- ✅ Возврат 404 для несуществующих бронирований
- ✅ Статус код 201 Created при успешном создании

### Примеры тестов:

```python
def test_create_booking():
    booking_data = {
        "firstname": "Test",
        "lastname": "User",
        "totalprice": 5000,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-09-01",
            "checkout": "2026-09-05"
        }
    }
    
    response = requests.post(
        "http://127.0.0.1:8000/booking",
        json=booking_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "bookingid" in data
    assert data["booking"]["firstname"] == "Test"


def test_get_nonexistent_booking():
    response = requests.get("http://127.0.0.1:8000/booking/999999")
    assert response.status_code == 404


def test_post_get_chain():
    # Создаём бронирование
    booking_data = {
        "firstname": "Chain",
        "lastname": "Test",
        "totalprice": 10000,
        "depositpaid": False,
        "bookingdates": {
            "checkin": "2026-10-01",
            "checkout": "2026-10-03"
        }
    }
    
    create_response = requests.post(
        "http://127.0.0.1:8000/booking",
        json=booking_data
    )
    
    booking_id = create_response.json()["bookingid"]
    
    # Получаем созданное бронирование
    get_response = requests.get(f"http://127.0.0.1:8000/booking/{booking_id}")
    
    assert get_response.status_code == 200
    assert get_response.json()["firstname"] == "Chain"
```

---

## 🔍 Просмотр истории запросов

Сервер автоматически логирует все входящие запросы. Это полезно для отладки и проверки webhook'ов.

### Способы просмотра:

**1. Через Swagger UI (рекомендуется)**
- Откройте http://127.0.0.1:8000/docs
- Найдите эндпоинт `GET /inspector/history`
- Нажмите "Try it out" → "Execute"

**2. Прямой URL в браузере**
```
http://127.0.0.1:8000/inspector/history?limit=50
```

Параметр `limit` (1-200) определяет количество последних запросов.

**3. Статистика сервера**
```
http://127.0.0.1:8000/inspector/stats
```

### Пример ответа с query parameters:

```json
{
  "total_requests": 5,
  "returned_count": 1,
  "limit": 1,
  "history": [
    {
      "id": "uuid...",
      "timestamp": "2026-07-07T12:00:00",
      "method": "GET",
      "url": "http://127.0.0.1:8000/entities?page=1&limit=50",
      "path": "/entities",
      "query_string": "page=1&limit=50",
      "query_params": {"page": "1", "limit": "50"},
      "query_params_multi": {},
      "headers": {...},
      "response_status": 200
    }
  ]
}
```

**Поля в истории:**
- `query_string` - сырая строка query параметров (сохраняет все дубликаты)
- `query_params` - словарь с последними значениями (стандартное поведение dict)
- `query_params_multi` - множественные значения для повторяющихся ключей

---

## 🔄 Множественные query параметры

Сервер поддерживает работу с повторяющимися query параметрами (например, `?filter=a&filter=b&filter=c`).

### Эндпоинт для тестирования:

**GET /entities/search**

Примеры использования:

```python
import requests

# Один фильтр
requests.get("http://127.0.0.1:8000/entities/search", params={"filter": "active"})

# Несколько фильтров с одинаковым ключом
query = [("filter", "active"), ("filter", "featured"), ("filter", "sale")]
requests.get("http://127.0.0.1:8000/entities/search", params=query)

# Ответ сервера:
# {
#   "message": "Search completed",
#   "filters_received": {
#     "filter": ["active", "featured", "sale"],
#     "tag": [],
#     "category": []
#   },
#   "total_filters": 3
# }
```

### Как это работает:

1. **URL формируется правильно**: `?filter=active&filter=featured&filter=sale`
2. **FastAPI сохраняет все значения**: через метод `request.query_params.getlist("filter")`
3. **В истории запросов** поле `query_params_multi` содержит списки значений для повторяющихся ключей

### Проверка в тестах:

```python
def test_multiple_query_params():
    query = [("filter", "active"), ("filter", "featured")]
    response = requests.get(
        "http://127.0.0.1:8000/entities/search",
        params=query
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "active" in data["filters_received"]["filter"]
    assert "featured" in data["filters_received"]["filter"]
    assert data["total_filters"] == 2
```

---

## 🗑️ Очистка истории запросов

**1. Через браузер:**
```
http://127.0.0.1:8000/inspector/history/clear
```

**2. Через curl:**
```bash
curl http://127.0.0.1:8000/inspector/history/clear
```

**3. Удалить файл вручную (сервер должен быть остановлен):**
```bash
rm data/request_history.json
```

---

**Готово к использованию!** 🎉
