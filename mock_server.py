"""
Модернизированный мок-сервер на FastAPI с персистентным хранением и валидацией.

Улучшения:
- Данные сохраняются в JSON файлы (персистентность)
- Валидация входящих данных
- История запросов также сохраняется
- Поддержка пагинации
- Улучшенная обработка ошибок
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from data_store import DataStore, RequestHistoryStore
from validators import EntityValidator, RequestValidator, ValidationError

# Инициализация приложения
app = FastAPI(
    title="Enhanced Mock Server",
    description="Локальный сервер с персистентным хранением и валидацией данных",
    version="2.0.0"
)

# Инициализация хранилищ
entity_store = DataStore(storage_file="data/entities.json")
history_store = RequestHistoryStore(
    storage_file="data/request_history.json",
    max_history=1000
)

# Хранилище бронирований (в памяти)
bookings_db: Dict[int, Dict[str, Any]] = {}
booking_id_counter: int = 1


# ============================================================================
# Pydantic модели для валидации
# ============================================================================

class EntityCreate(BaseModel):
    """Модель для создания сущности"""
    name: Optional[str] = Field(None, max_length=200, description="Имя сущности")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")


class EntityUpdate(BaseModel):
    """Модель для обновления сущности"""
    name: Optional[str] = Field(None, max_length=200, description="Новое имя сущности")
    data: Optional[Dict[str, Any]] = Field(None, description="Обновленные данные")


# ============================================================================
# МОДЕЛИ ДЛЯ БРОНИРОВАНИЙ
# ============================================================================

class BookingDates(BaseModel):
    """Модель дат бронирования"""
    checkin: str = Field(..., description="Дата заезда (YYYY-MM-DD)")
    checkout: str = Field(..., description="Дата выезда (YYYY-MM-DD)")


class BookingCreate(BaseModel):
    """Модель для создания бронирования"""
    firstname: str = Field(..., min_length=1, max_length=100, description="Имя")
    lastname: str = Field(..., min_length=1, max_length=100, description="Фамилия")
    totalprice: int = Field(..., ge=0, description="Общая стоимость")
    depositpaid: bool = Field(..., description="Оплачен ли депозит")
    bookingdates: BookingDates = Field(..., description="Даты бронирования")
    additionalneeds: Optional[str] = Field("None", description="Дополнительные потребности")


# ============================================================================
# Middleware для логирования запросов
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех входящих запросов"""
    
    # Сохраняем информацию о запросе
    request_info = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_string": str(request.url.query),  # Сырая строка query params
        "query_params": dict(request.query_params),  # Для совместимости (последние значения)
        "query_params_multi": {},  # Множественные значения
        "headers": dict(request.headers),
        "client_host": request.client.host if request.client else None,
    }

    # Получаем все значения для повторяющихся ключей
    for key in set(request.query_params.keys()):
        values = request.query_params.getlist(key)
        if len(values) > 1:
            request_info["query_params_multi"][key] = values

    # Читаем тело запроса (если есть)
    try:
        body = await request.body()
        if body:
            try:
                request_info["body"] = body.decode('utf-8')
            except:
                request_info["body"] = body.hex()
    except:
        request_info["body"] = None

    # Обрабатываем запрос
    response = await call_next(request)

    # Добавляем информацию об ответе
    request_info["response_status"] = response.status_code
    request_info["response_headers"] = dict(response.headers)

    # Сохраняем в историю
    history_store.add(request_info)

    return response


# ============================================================================
# Endpoints для работы с сущностями
# ============================================================================

@app.post("/entities", status_code=201)
async def create_entity(entity: EntityCreate):
    """
    Создание новой сущности с валидацией
    
    - **name**: имя сущности (опционально, макс. 200 символов)
    - **data**: дополнительные данные в формате JSON (опционально)
    
    Возвращает статус 201 Created и сгенерированный ID
    """
    try:
        # Валидация данных
        validated_data = EntityValidator.validate_create(entity.dict())
        
        # Генерация ID
        entity_id = str(uuid.uuid4())
        
        # Создание сущности
        new_entity = entity_store.create(entity_id, validated_data)
        
        return {
            "id": entity_id,
            "message": "Entity created successfully",
            "entity": new_entity
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """
    Получение сущности по ID
    
    - **entity_id**: UUID сущности
    """
    entity = entity_store.get(entity_id)
    
    if not entity:
        raise HTTPException(
            status_code=404, 
            detail=f"Entity with id '{entity_id}' not found"
        )
    
    return entity


@app.get("/entities/search")
async def search_entities(request: Request):
    """
    Поиск сущностей с поддержкой множественных фильтров
    
    Пример использования:
    - /entities/search?filter=active&filter=featured&filter=sale
    - /entities/search?tag=python&tag=testing
    
    Возвращает все полученные фильтры для демонстрации работы с множественными параметрами
    """
    # Получаем ВСЕ значения для каждого ключа
    filters = request.query_params.getlist("filter")
    tags = request.query_params.getlist("tag")
    categories = request.query_params.getlist("category")
    
    result = {
        "message": "Search completed",
        "filters_received": {
            "filter": filters if filters else [],
            "tag": tags if tags else [],
            "category": categories if categories else []
        },
        "total_filters": len(filters) + len(tags) + len(categories)
    }
    
    return result


@app.get("/entities")
async def list_entities(
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Количество элементов на странице")
):
    """
    Получение списка всех сущностей с пагинацией
    
    - **page**: номер страницы (по умолчанию 1)
    - **limit**: количество элементов (по умолчанию 50, макс. 100)
    """
    all_entities = entity_store.get_all()
    total_count = len(all_entities)
    
    # Пагинация
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_entities = all_entities[start_idx:end_idx]
    
    return {
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 0,
        "entities": paginated_entities
    }


@app.put("/entities/{entity_id}")
async def update_entity(entity_id: str, update_data: EntityUpdate):
    """
    Обновление сущности по ID
    
    - **entity_id**: UUID сущности
    - **name**: новое имя (опционально)
    - **data**: новые данные (опционально)
    """
    try:
        # Проверяем существование
        existing = entity_store.get(entity_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Entity with id '{entity_id}' not found"
            )
        
        # Валидация данных
        validated_data = EntityValidator.validate_update(update_data.dict(exclude_unset=True))
        
        # Обновление
        updated_entity = entity_store.update(entity_id, validated_data)
        
        return {
            "message": "Entity updated successfully",
            "entity": updated_entity
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    """
    Удаление сущности по ID
    
    - **entity_id**: UUID сущности
    """
    deleted_entity = entity_store.delete(entity_id)
    
    if not deleted_entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity with id '{entity_id}' not found"
        )
    
    return {
        "message": "Entity deleted successfully",
        "entity": deleted_entity
    }


# ============================================================================
# Endpoints для работы с историей запросов
# ============================================================================

@app.get("/inspector/history")
async def get_request_history(
    limit: int = Query(50, ge=1, le=200, description="Количество последних запросов")
):
    """
    Получение истории всех запросов
    
    - **limit**: количество последних запросов (1-200, по умолчанию 50)
    """
    recent_requests = history_store.get_recent(limit)
    
    return {
        "total_requests": history_store.count(),
        "returned_count": len(recent_requests),
        "limit": limit,
        "history": recent_requests
    }


@app.get("/inspector/history/clear")
async def clear_request_history():
    """Очистка истории запросов"""
    history_store.clear()
    return {"message": "Request history cleared"}


@app.get("/inspector/stats")
async def get_server_stats():
    """Получение статистики сервера"""
    return {
        "total_entities": entity_store.count(),
        "total_bookings": len(bookings_db),
        "total_requests_logged": history_store.count(),
        "server_uptime": "N/A",  # Можно добавить отслеживание времени запуска
        "storage_location": str(entity_store.storage_file.absolute()),
        "history_location": str(history_store.storage_file.absolute())
    }


# ============================================================================
# ЭНДПОИНТЫ ДЛЯ БРОНИРОВАНИЙ
# ============================================================================

@app.post("/booking", status_code=201)
def create_booking(booking: BookingCreate):
    """
    Создаёт новое бронирование
    
    Требования:
    - Принимает JSON с данными бронирования
    - Генерирует уникальный bookingid
    - Возвращает bookingid и данные бронирования
    - Статус код: 201 Created
    
    Пример тела запроса:
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
    """
    global booking_id_counter
    
    booking_id = booking_id_counter
    booking_id_counter += 1
    
    # Сохраняем в "базу данных"
    bookings_db[booking_id] = booking.dict()
    
    print(f"✅ Создано бронирование ID={booking_id}: {booking.dict()}")
    
    return {
        "bookingid": booking_id,
        "booking": booking.dict()
    }


@app.get("/booking/{booking_id}")
def get_booking(booking_id: int):
    """
    Получает бронирование по ID
    
    Требования:
    - Возвращает данные бронирования если существует
    - Возвращает 404 если не найдено
    - Статус код: 200 OK или 404 Not Found
    """
    if booking_id not in bookings_db:
        raise HTTPException(
            status_code=404, 
            detail=f"Booking with id {booking_id} not found"
        )
    
    print(f"✅ Получено бронирование ID={booking_id}")
    return bookings_db[booking_id]


@app.delete("/booking/{booking_id}")
def delete_booking(booking_id: int):
    """
    Удаляет бронирование по ID (опционально)
    """
    if booking_id not in bookings_db:
        raise HTTPException(
            status_code=404, 
            detail=f"Booking with id {booking_id} not found"
        )
    
    del bookings_db[booking_id]
    print(f"✅ Удалено бронирование ID={booking_id}")
    
    return {"message": f"Booking {booking_id} deleted successfully"}


# ============================================================================
# Системные endpoints
# ============================================================================

@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о сервере"""
    return {
        "service": "Enhanced Mock Server",
        "version": "2.0.0",
        "features": [
            "Persistent storage (JSON files)",
            "Data validation",
            "Request history logging",
            "Pagination support",
            "Multiple query parameters support",
            "Booking management API",
            "Swagger UI documentation"
        ],
        "endpoints": {
            "POST /entities": "Создать новую сущность (с валидацией)",
            "GET /entities": "Получить список всех сущностей (с пагинацией)",
            "GET /entities/{id}": "Получить сущность по ID",
            "PUT /entities/{id}": "Обновить сущность по ID",
            "DELETE /entities/{id}": "Удалить сущность по ID",
            "GET /entities/search": "Поиск с множественными фильтрами",
            "POST /booking": "Создать бронирование",
            "GET /booking/{id}": "Получить бронирование по ID",
            "DELETE /booking/{id}": "Удалить бронирование",
            "GET /inspector/history": "Просмотреть историю запросов",
            "GET /inspector/history/clear": "Очистить историю запросов",
            "GET /inspector/stats": "Статистика сервера",
            "GET /docs": "Swagger UI интерфейс"
        },
        "swagger_ui": "http://127.0.0.1:8000/docs",
        "request_history": "http://127.0.0.1:8000/inspector/history",
        "stats": "http://127.0.0.1:8000/inspector/stats"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Обработчики ошибок
# ============================================================================

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Обработчик ошибок валидации"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Enhanced Mock Server v2.0 запущен!")
    print("=" * 70)
    print("📖 Swagger UI:        http://127.0.0.1:8000/docs")
    print("📋 История запросов:   http://127.0.0.1:8000/inspector/history")
    print("📊 Статистика:         http://127.0.0.1:8000/inspector/stats")
    print("🏠 Главная страница:   http://127.0.0.1:8000/")
    print("💾 Хранилище:          data/entities.json")
    print("📝 История:            data/request_history.json")
    print("=" * 70)
    print("✨ Особенности:")
    print("   ✅ Персистентное хранение данных")
    print("   ✅ Валидация входящих данных")
    print("   ✅ Пагинация списков")
    print("   ✅ Логирование всех запросов")
    print("   ✅ Множественные query параметры")
    print("   ✅ API для работы с бронированиями")
    print("=" * 70)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
