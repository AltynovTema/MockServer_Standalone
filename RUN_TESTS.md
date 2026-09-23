# Запуск тестов Mock Server v2.0

## Требования

```bash
pip install -r requirements.txt
```

## Запуск сервера

Перед запуском тестов необходимо запустить мок-сервер:

```bash
python mock_server.py
```

Сервер будет доступен по адресу: `http://127.0.0.1:8000`

Swagger UI: `http://127.0.0.1:8000/docs`

## Запуск тестов

### Все тесты (62 шт.)

```bash
pytest test/test_api.py
```

### С расширенным выводом

```bash
pytest test/test_api.py -v
```

### С выводом времени выполнения

```bash
pytest test/test_api.py -v --durations=10
```

### Только позитивные тесты

```bash
pytest test/test_api.py::TestPositive -v
```

### Только негативные тесты

```bash
pytest test/test_api.py::TestNegative -v
```

### Только тесты авторизации

```bash
pytest test/test_api.py::TestAuthPositive -v
pytest test/test_api.py::TestAuthNegative -v
```

### Только тесты ролевой системы (RBAC)

```bash
pytest test/test_api.py::TestRolesPositive -v
pytest test/test_api.py::TestRolesNegative -v
```

### Конкретный тест

```bash
pytest test/test_api.py::TestRolesPositive::test_login_superadmin_has_all_roles -v
```

### С остановкой при первом падении

```bash
pytest test/test_api.py -v -x
```

### С детальным выводом при падении

```bash
pytest test/test_api.py -v -vv
```

## Структура тестов

| Класс | Кол-во | Описание |
|-------|--------|----------|
| **TestPositive** | 23 | Позитивные тесты (TC-001 … TC-023) |
| **TestNegative** | 6 | Негативные тесты (TC-N001 … TC-N006) |
| **TestAuthPositive** | 7 | Позитивные тесты авторизации (TC-A001 … TC-A007) |
| **TestAuthNegative** | 8 | Негативные тесты авторизации (TC-A008 … TC-A014) |
| **TestRolesPositive** | 10 | Позитивные тесты ролей (TC-R001 … TC-R010) |
| **TestRolesNegative** | 10 | Негативные тесты ролей (TC-R011 … TC-R020) |

**Итого: 62 теста**

## Тестовые пользователи

| Логин | Пароль | Роли | Права |
|-------|--------|------|-------|
| `superadmin` | `superadmin123` | `["USER", "ADMIN", "SUPER_ADMIN"]` | Полный доступ |
| `admin` | `admin123` | `["USER", "ADMIN"]` | Управление пользователями + всё USER |
| `user` | `user123` | `["USER"]` | Просмотр, отзывы, оплата |

## Ролевая модель

```
SUPER_ADMIN (уровень 2)
  ├── entities:create / update / delete
  ├── genres:crUD
  ├── users:crUD
  └── всё из USER

ADMIN (уровень 1)
  ├── users:read / update / delete
  └── всё из USER

USER (уровень 0)
  ├── entities:read
  ├── reviews:create
  └── tickets:pay
```

Каждая следующая роль включает **все** права предыдущих.

## Разделение эндпоинтов по доступу

### Публичные (без авторизации)
- `GET /` — информация о сервере
- `GET /health` — health check
- `GET /entities` — список сущностей
- `GET /entities/{id}` — получение сущности
- `GET /entities/search` — поиск
- `GET /inspector/history` — история запросов
- `GET /inspector/history/clear` — очистка истории
- `GET /inspector/stats` — статистика

### Требуют авторизации (любой токен)
- `GET /protected/data` — защищённые данные
- `GET /auth/me` — профиль пользователя

### Требуют SUPER_ADMIN
- `POST /entities` — создание сущности
- `PUT /entities/{id}` — обновление сущности
- `DELETE /entities/{id}` — удаление сущности

### Аутентификация (общие)
- `POST /auth/login` — вход, получение токенов
- `POST /auth/refresh` — обновление токенов
- `POST /auth/logout` — выход, отзыв токена
- `GET /auth/validate` — проверка токена

## Покрытие эндпоинтов

| Эндпоинт | GET (без токена) | USER | ADMIN | SUPER_ADMIN |
|----------|:-:|:-:|:-:|:-:|
| `GET /` | ✅ | ✅ | ✅ | ✅ |
| `GET /health` | ✅ | ✅ | ✅ | ✅ |
| `GET /entities` | ✅ | ✅ | ✅ | ✅ |
| `GET /entities/{id}` | ✅ | ✅ | ✅ | ✅ |
| `POST /entities` | ❌ 401 | ❌ 403 | ❌ 403 | ✅ 201 |
| `PUT /entities/{id}` | ❌ 401 | ❌ 403 | ❌ 403 | ✅ 200 |
| `DELETE /entities/{id}` | ❌ 401 | ❌ 403 | ❌ 403 | ✅ 200 |
| `POST /booking` | ✅ | ✅ | ✅ | ✅ |
| `GET /booking/{id}` | ✅ | ✅ | ✅ | ✅ |
| `DELETE /booking/{id}` | ✅ | ✅ | ✅ | ✅ |
| `GET /protected/data` | ❌ 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| `GET /auth/me` | ❌ 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/refresh` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/logout` | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/validate` | ✅ | ✅ | ✅ | ✅ |

## Примеры ручных проверок

### Получить токен SUPER_ADMIN
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"superadmin123"}'
```

### Создать сущность (требует SUPER_ADMIN)
```bash
TOKEN="<access_token>"
curl -X POST http://127.0.0.1:8000/entities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestEntity","data":{"key":"value"}}'
```

### Проверить профиль пользователя
```bash
TOKEN="<access_token>"
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Проверить что USER не может создать сущность
```bash
TOKEN="<user_token>"
curl -X POST http://127.0.0.1:8000/entities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test"}'
# Ожидаемый ответ: 403 Access denied. Required permission: 'entities:create'
```
