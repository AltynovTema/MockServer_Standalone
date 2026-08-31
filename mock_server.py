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
import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from data_store import DataStore, RequestHistoryStore, TokenStore
from validators import EntityValidator, RequestValidator, ValidationError, TokenUtils
from fastapi import Depends
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
# ЗАВИСИМОСТЬ ДЛЯ ВАЛИДАЦИИ JWT ТОКЕНА
# ============================================================================

from fastapi import Header, status


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer токен в заголовке Authorization")
) -> Dict[str, Any]:
    """
    FastAPI зависимость для валидации Bearer access токена.
    
    Использует:
    1. Проверку JWT подписи и срока действия через python-jose
    2. Проверку что токен не отозван через TokenStore
    
    Возвращает словарь с user_id и ролью.
    Выбрасывает HTTPException 401 при любой ошибке.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует заголовок Authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Извлекаем токен из "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат заголовка Authorization. Используйте: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Декодируем JWT
    payload = TokenUtils.decode_token(token, expected_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access токен недействителен или истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем что токен не отозван в TokenStore
    token_data = token_store.validate_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access токен отозван или истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role", "user"),
        "token_jti": token_data["token_id"],
    }

# ============================================================================
# КОНФИГУРАЦИЯ АВТОРИЗАЦИИ
# ============================================================================

# Секретный ключ для подписи JWT (по умолчанию для демо)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mock-server-secret-key-for-training-only")
JWT_ALGORITHM = "HS256"

# Время жизни токенов (в секундах)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "60"))

# Тестовые пользователи (для обучения)
TEST_USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
    },
    "user": {
        "password": "user123",
        "role": "user",
    },
}

# Инициализация хранилища токенов
token_store = TokenStore()


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
# МОДЕЛИ ДЛЯ АВТОРИЗАЦИИ
# ============================================================================

class LoginRequest(BaseModel):
    """Модель для запроса входа"""
    username: str = Field(..., min_length=1, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=1, description="Пароль")


class TokenResponse(BaseModel):
    """Модель ответа с токенами"""
    access_token: str = Field(..., description="JWT access токен")
    refresh_token: str = Field(..., description="JWT refresh токен")
    token_type: str = Field("bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время жизни access токена в секундах")


class TokenRefreshRequest(BaseModel):
    """Модель для запроса обновления токена"""
    refresh_token: str = Field(..., description="Действующий refresh токен")


class TokenValidationResponse(BaseModel):
    """Модель ответа валидации токена"""
    valid: bool = Field(..., description="Валиден ли токен")
    token_type: Optional[str] = Field(None, description="Тип токена")
    user_id: Optional[str] = Field(None, description="ID пользователя")
    expired: Optional[bool] = Field(None, description="Истёк ли токен")
    revoked: Optional[bool] = Field(None, description="Отозван ли токен")
    expires_at: Optional[str] = Field(None, description="Дата истечения")
    message: str = Field(..., description="Описание статуса")


class LogoutRequest(BaseModel):
    """Модель для запроса выхода"""
    token: Optional[str] = Field(None, description="Токен для отзыва (access или refresh)")


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

    # Проверяем наличие флага замедления в запросе
    if "slow" in request.query_params:
        try:
            delay = float(request.query_params["slow"])
            if delay < 0:
                delay = 0
        except ValueError:
            delay = 1  # Значение по умолчанию - 1 секунда
        await asyncio.sleep(delay)

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
async def create_entity(request: Request):
    """
    Создание новой сущности с валидацией
    
    Поддерживает как JSON, так и form-encoded данные
    
    Возвращает статус 201 Created и сгенерированный ID
    """
    try:
        # Определяем тип контента и парсим данные соответствующим образом
        content_type = request.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            raw_data = await request.json()
            if not raw_data:
                raise HTTPException(
                    status_code=400,
                    detail="Request body cannot be empty. Provide valid JSON data."
                )


        elif "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            raw_data = dict(form_data)
        else:
            raise HTTPException(
                status_code=415, 
                detail="Unsupported Media Type. Use JSON or form-encoded data."
            )
        
        # Валидация данных
        validated_data = EntityValidator.validate_create(raw_data)
        
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
async def create_booking(request: Request, booking: BookingCreate):
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
    
    Также поддерживает параметры:
    - SlowPerformance (bool): если true, вводит задержку в ответе
    - DelaySeconds (int): длительность задержки в секундах
    """
    global booking_id_counter
    


    booking_id = booking_id_counter
    booking_id_counter += 1
    
    # Сохраняем в "базу данных"
    bookings_db[booking_id] = booking.dict()
    
    print(f"✅ Создано бронирование ID={booking_id}: {booking.dict()}")
    
    # Формируем ответ
    response = {
        "bookingid": booking_id,
        "booking": booking.dict()
    }
    

    
    return response


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
# ЭНДПОИНТЫ АВТОРИЗАЦИИ
# ============================================================================

@app.post("/auth/login", response_model=TokenResponse, status_code=200)
async def login(request: LoginRequest):
    """
    Аутентификация пользователя и получение пары токенов.
    
    - **username**: имя пользователя (admin или user)
    - **password**: пароль
    
    Возвращает:
    - access_token (живёт 5 минут)
    - refresh_token (живёт 60 минут)
    - token_type: "bearer"
    - expires_in: время жизни access токена в секундах
    
    Тестовые пользователи:
    - admin / admin123
    - user / user123
    """
    # Проверяем учётные данные
    user_data = TEST_USERS.get(request.username)
    if not user_data or user_data["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    
    user_id = request.username
    role = user_data["role"]
    
    # Вычисляем время истечения
    access_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    # Создаём JWT токены
    access_token = TokenUtils.create_access_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = TokenUtils.create_refresh_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    
    # Сохраняем метаданные в TokenStore
    token_store.store_access_token(access_token, user_id, access_expires)
    token_store.store_refresh_token(refresh_token, user_id, refresh_expires)
    
    print(f"✅ Пользователь '{user_id}' вошёл в систему")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/auth/refresh", response_model=TokenResponse, status_code=200)
async def refresh_token_endpoint(request: TokenRefreshRequest):
    """
    Обновление токенов с ротацией refresh токена.
    
    - Принимает действующий refresh токен
    - Отзывает старый refresh токен (ротация)
    - Выдаёт новую пару access + refresh токенов
    - Старый access токен также отзывается
    
    Best Practice: ротация refresh токена предотвращает кражу сессии.
    """
    # Декодируем refresh токен
    payload = TokenUtils.decode_token(request.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен недействителен или истёк",
        )
    
    user_id = payload.get("sub")
    
    # Проверяем что refresh токен не отозван
    token_data = token_store.validate_refresh_token(request.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен отозван или истёк. Требуется повторный вход.",
        )
    
    # Генерируем новые токены
    access_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    new_access = TokenUtils.create_access_token(
        data={"sub": user_id, "role": payload.get("role", "user")},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh = TokenUtils.create_refresh_token(
        data={"sub": user_id, "role": payload.get("role", "user")},
        expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    
    # Ротируем: отзываем старый refresh, сохраняем новые
    token_store.rotate_refresh_token(
        old_refresh_token=request.refresh_token,
        new_access=new_access,
        new_refresh=new_refresh,
        user_id=user_id,
        access_expires=access_expires,
        refresh_expires=refresh_expires,
    )
    
    print(f"✅ Токены обновлены для пользователя '{user_id}' (ротация)")
    
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/auth/logout", status_code=200)
async def logout(request: LogoutRequest):
    """
    Выход из системы - отзыв токена.
    
    - Отзывает указанный токен (access или refresh)
    - Токен немедленно становится недействительным
    - Если token не указан, отзываются все токены пользователя из заголовка
    """
    if not request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите токен для отзыва в поле 'token'",
        )
    
    revoked = token_store.revoke_token(request.token)
    
    if revoked:
        print(f"🔒 Токен отозван (logout)")
        return {"message": "Успешный выход. Токен отозван."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен не найден или уже отозван",
        )


@app.get("/auth/validate", response_model=TokenValidationResponse)
async def validate_token(token: str = Query(..., description="Токен для проверки")):
    """
    Проверка статуса токена. Полезно для отладки во время обучения.
    
    Возвращает:
    - valid: валиден ли токен
    - token_type: тип токена (access/refresh)
    - expired: истёк ли токен
    - revoked: отозван ли токен
    - user_id: владелец токена
    - expires_at: дата истечения
    - message: описание статуса
    """
    token_info = token_store.get_token_info(token)
    
    if token_info is None:
        # Проверяем JWT структуру
        jwt_payload = TokenUtils.decode_token(token, expected_type="access")
        if jwt_payload is None:
            jwt_payload = TokenUtils.decode_token(token, expected_type="refresh")
        
        if jwt_payload is None:
            return TokenValidationResponse(
                valid=False,
                message="Токен не найден и не является валидным JWT",
            )
        else:
            return TokenValidationResponse(
                valid=False,
                token_type=jwt_payload.get("type"),
                user_id=jwt_payload.get("sub"),
                expired=False,
                revoked=True,
                message="Токен валиден по JWT, но отозван в хранилище",
            )
    
    is_expired = datetime.utcnow() > datetime.fromisoformat(token_info["expires_at"].replace("+00:00", ""))
    is_valid = not token_info["revoked"] and not is_expired
    
    if is_valid:
        message = "Токен валиден"
    elif token_info["revoked"]:
        message = "Токен отозван"
    else:
        message = "Токен истёк"
    
    return TokenValidationResponse(
        valid=is_valid,
        token_type=token_info["token_type"],
        user_id=token_info["user_id"],
        expired=is_expired,
        revoked=token_info["revoked"],
        expires_at=token_info["expires_at"],
        message=message,
    )


@app.get("/protected/data")
async def get_protected_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Защищённый ресурс - требует валидный Bearer access токен.
    
    Демонстрирует использование FastAPI Depends() для защиты эндпоинта.
    Возвращает 401 при отсутствии или невалидном токене.
    """
    return {
        "message": "Доступ к защищённым данным получен!",
        "user_id": current_user["user_id"],
        "role": current_user["role"],
        "sensitive_data": {
            "api_key": "demo-key-12345",
            "user_profile": {
                "id": current_user["user_id"],
                "role": current_user["role"],
                "permissions": ["read", "write"] if current_user["role"] == "admin" else ["read"],
            },
        },
    }


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
            "Swagger UI documentation",
            "JWT authentication (access + refresh tokens)",
            "Token rotation on refresh",
            "Protected resource endpoints"
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
            "GET /docs": "Swagger UI интерфейс",
            "POST /auth/login": "Аутентификация и получение токенов",
            "POST /auth/refresh": "Обновление токенов (ротация)",
            "POST /auth/logout": "Выход - отзыв токена",
            "GET /auth/validate": "Проверка статуса токена",
            "GET /protected/data": "Защищённый ресурс (требуется Bearer токен)"
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
    print("🔐 Аутентификация:     http://127.0.0.1:8000/auth/login")
    print("🔄 Обновление токенов: http://127.0.0.1:8000/auth/refresh")
    print("🔒 Защищённые данные:  http://127.0.0.1:8000/protected/data")
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
    print("   ✅ JWT аутентификация (access + refresh токены)")
    print("   ✅ Ротация refresh токенов")
    print("   ✅ Защищённые ресурсы с Bearer авторизацией")
    print("   ✅ Проверка статуса токенов")
    print("=" * 70)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
