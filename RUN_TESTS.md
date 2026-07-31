# Запуск тестов

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

## Запуск тестов

### Все тесты

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

### Конкретный тест

```bash
pytest test/test_api.py::TestPositive::test_get_root_endpoint -v
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

- **TestPositive**: 22 позитивных теста (TC-001 ... TC-022)
- **TestNegative**: 6 негативных тестов (TC-N001 ... TC-N006)

## Покрытие

Тесты покрывают следующие эндпоинты:

- `GET /` - корневой эндпоинт
- `GET /health` - health check
- `POST /entities` - создание сущности
- `GET /entities/{id}` - получение сущности
- `GET /entities` - список сущностей (пагинация)
- `PUT /entities/{id}` - обновление сущности
- `DELETE /entities/{id}` - удаление сущности
- `POST /booking` - создание бронирования
- `GET /booking/{id}` - получение бронирования
- `DELETE /booking/{id}` - удаление бронирования
- `GET /inspector/history` - история запросов
- `GET /inspector/history/clear` - очистка истории
- `GET /inspector/stats` - статистика сервера
