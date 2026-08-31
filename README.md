# Enhanced Mock Server v2.0 - Standalone Project

Отдельный проект мок-сервера для использования в учебных модулях.

## 📁 Структура проекта

```
MockServer_Standalone/
├── mock_server.py          # Основной сервер
├── data_store.py           # Хранилище данных и токенов
├── validators.py           # Валидация и JWT утилиты
├── requirements.txt        # Зависимости
├── start.sh               # Запуск (macOS/Linux)
├── start.bat              # Запуск (Windows)
├── .gitignore
├── README.md
├── RUN_TESTS.md           # Инструкция по тестам
└── data/                  # Данные сервера
    ├── entities.json
    └── request_history.json
└── test/                  # Тесты
    ├── conftest.py
    └── test_api.py
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

## 🔐 JWT Аутентификация

Сервер поддерживает полный цикл работы с JWT токенами для тренировки навыков OAuth 2.0.

### Тестовые пользователи

| Username | Password | Role   |
|----------|----------|--------|
| admin    | admin123 | admin  |
| user     | user123  | user   |

### Эндпоинты аутентификации

#### `POST /auth/login` — Вход и получение токенов

Получает пару токенов: access (5 минут) и refresh (60 минут).

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/auth/login",
    json={"username": "admin", "password": "admin123"}
)

# Ответ:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer",
#   "expires_in": 300
# }
```

#### `POST /auth/refresh` — Обновление токенов с ротацией

Обновляет пару токенов, отзывая старый refresh токен (ротация).

```python
refresh_response = requests.post(
    "http://127.0.0.1:8000/auth/refresh",
    json={"refresh_token": "старый_refresh_токен"}
)

# Ответ: новая пара токенов
# Старый refresh токен больше не работает!
```

#### `POST /auth/logout` — Выход и отзыв токена

Немедленно отзывает указанный токен.

```python
response = requests.post(
    "http://127.0.0.1:8000/auth/logout",
    json={"token": "access_или_refresh_токен"}
)

# Ответ: {"message": "Успешный выход. Токен отозван."}
```

#### `GET /auth/validate` — Проверка статуса токена

Проверяет валидность, срок действия и статус отзыва токена.

```python
response = requests.get(
    "http://127.0.0.1:8000/auth/validate",
    params={"token": "токен_для_проверки"}
)

# Ответ:
# {
#   "valid": true,
#   "token_type": "access",
#   "user_id": "admin",
#   "expired": false,
#   "revoked": false,
#   "expires_at": "2026-08-31T15:26:51.603924",
#   "message": "Токен валиден"
# }
```

#### `GET /protected/data` — Защищённый ресурс

Требует валидный Bearer access токен.

```python
access_token = "полученный_access_токен"

response = requests.get(
    "http://127.0.0.1:8000/protected/data",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Ответ:
# {
#   "message": "Доступ к защищённым данным получен!",
#   "user_id": "admin",
#   "role": "admin",
#   "sensitive_data": {
#     "api_key": "demo-key-12345",
#     "user_profile": {
#       "id": "admin",
#       "role": "admin",
#       "permissions": ["read", "write"]
#     }
#   }
# }
```

### Сценарии для тренировки

1. **Получение токенов** — логин и получение access + refresh токенов
2. **Использование токена** — запрос защищённых данных с Bearer авторизацией
3. **Истечение access токена** — подождать 5 минут и получить 401
4. **Обновление токенов** — использовать refresh токен для получения новой пары
5. **Ротация refresh токена** — стар refresh токен становится невалидным после обновления
6. **Истечение refresh токена** — подождать 60 минут и потребовать повторный вход
7. **Отзыв токена** — logout и немедленная невалидность токена

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
✅ **JWT аутентификация** - полный цикл OAuth 2.0  
✅ **Ротация токенов** - безопасность сессий  

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

**POST /booking** - Создание бронировани��
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

---

## 🧪 Запуск тестов

```bash
# Запустить все тесты
pytest test/test_api.py -v

# Запустить только позитивные тесты
pytest test/test_api.py::TestPositive -v

# Запустить только негативные тесты
pytest test/test_api.py::TestNegative -v

# Запустить тесты аутентификации
pytest test/test_api.py::TestAuthPositive -v
pytest test/test_api.py::TestAuthNegative -v
```

Подробнее: [RUN_TESTS.md](RUN_TESTS.md)

---

## 📦 Git — Загрузка на репозиторий

### Инициализация репозитория (если ещё не инициализирован)

```bash
# Инициализировать git репозиторий
git init

# Добавить удалённый репозиторий (замените URL на ваш)
git remote add origin https://github.com/ваш-username/имя-репозитория.git
```

### Добавление и коммит изменений

```bash
# Проверить статус файлов
git status

# Добавить все файлы для коммита
git add .

# Создать коммит с описанием
git commit -m "Enhanced Mock Server v2.0 - JWT auth, persistent storage, validation"
```

### Загрузка на удалённый репозиторий

```bash
# Загрузить на main ветку
git push -u origin main

# Или на master ветку
git push -u origin master
```

### Работа с существующим репозиторием

```bash
# Добавить конкретный файл
git add mock_server.py

# Добавить все изменённые файлы
git add -A

# Коммит с подробным описанием
git commit -m "Add JWT authentication with refresh token rotation

- Added login endpoint with access/refresh tokens
- Implemented token rotation on refresh
- Added protected resource endpoint
- Added token validation and revocation
- 14 new auth tests (7 positive, 7 negative)"

# Загрузить изменения
git push

# Получить последние изменения с удалённого репозитория
git pull origin main
```

### Полезные команды

```bash
# Посмотреть историю коммитов
git log --oneline

# Посмотреть изменения в файлах
git diff

# Отменить добавление файла из staging
git reset HEAD файл.py

# Удалить файл из репозитория
git rm файл.py
git commit -m "Remove unused file"

# Создать новую ветку
git checkout -b feature/new-endpoint

# Переключиться на ветку
git checkout main

# Слить изменения из ветки
git merge feature/new-endpoint
```

---

**Готово к использованию!** 🎉
