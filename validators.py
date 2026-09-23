"""
Модуль для валидации данных мок-сервера.
Содержит классы для валидации сущностей и запросов.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


class EntityValidator:
    """Валидатор для сущностей"""
    
    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных при создании сущности
        
        Args:
            data: Словарь с данными сущности
            
        Returns:
            Валидированные данные
            
        Raises:
            ValidationError: Если данные не прошли валидацию
        """
        validated = {}
        
        # Валидация имени
        if data.get("name") is not None:
            name = data["name"]
            if not isinstance(name, str):
                raise ValidationError("Name must be a string")
            if len(name) > 200:
                raise ValidationError("Name must not exceed 200 characters")
            if len(name.strip()) == 0:
                raise ValidationError("Name cannot be empty or whitespace only")
            validated["name"] = name.strip()
        
        # Валидация данных
        if data.get("data") is not None:
            entity_data = data["data"]
            if not isinstance(entity_data, dict):
                raise ValidationError("Data must be a JSON object (dictionary)")
            validated["data"] = entity_data
        
        return validated
    
    @staticmethod
    def validate_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных при обновлении сущности
        
        Args:
            data: Словарь с данными для обновления
            
        Returns:
            Валидированные данные
            
        Raises:
            ValidationError: Если данные не прошли валидацию
        """
        validated = {}
        
        # Валидация имени (если предоставлено)
        if "name" in data and data["name"] is not None:
            name = data["name"]
            if not isinstance(name, str):
                raise ValidationError("Name must be a string")
            if len(name) > 200:
                raise ValidationError("Name must not exceed 200 characters")
            if len(name.strip()) == 0:
                raise ValidationError("Name cannot be empty or whitespace only")
            validated["name"] = name.strip()
        
        # Валидация данных (если предоставлены)
        if "data" in data and data["data"] is not None:
            entity_data = data["data"]
            if not isinstance(entity_data, dict):
                raise ValidationError("Data must be a JSON object (dictionary)")
            validated["data"] = entity_data
        
        return validated


class RequestValidator:
    """Валидатор для входящих запросов"""
    
    @staticmethod
    def validate_pagination(page: int, limit: int) -> tuple[int, int]:
        """
        Валидация параметров пагинации
        
        Args:
            page: Номер страницы
            limit: Количество элементов на странице
            
        Returns:
            Кортеж (page, limit) с валидированными значениями
            
        Raises:
            ValidationError: Если параметры невалидны
        """
        if page < 1:
            raise ValidationError("Page number must be >= 1")
        if limit < 1:
            raise ValidationError("Limit must be >= 1")
        if limit > 100:
            raise ValidationError("Limit must not exceed 100")
        
        return page, limit
    
    @staticmethod
    def validate_history_limit(limit: int) -> int:
        """
        Валидация лимита для истории запросов
        
        Args:
            limit: Количество записей
            
        Returns:
            Валидированный лимит
            
        Raises:
            ValidationError: Если лимит невалиден
        """
        if limit < 1:
            raise ValidationError("History limit must be >= 1")
        if limit > 200:
            raise ValidationError("History limit must not exceed 200")
        
        return limit
    
    @staticmethod
    def validate_entity_id(entity_id: str) -> str:
        """
        Валидация ID сущности
        
        Args:
            entity_id: ID сущности
            
        Returns:
            Валидированный ID
            
        Raises:
            ValidationError: Если ID невалиден
        """
        if not entity_id or not isinstance(entity_id, str):
            raise ValidationError("Entity ID must be a non-empty string")
        if len(entity_id.strip()) == 0:
            raise ValidationError("Entity ID cannot be whitespace only")
        
        return entity_id.strip()


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С JWT ТОКЕНАМИ
# ============================================================================

# ============================================================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ РОЛЕЙ
# ============================================================================

# Иерархия ролей (индекс = уровень привилегий)
ROLE_HIERARCHY = {
    "USER": 0,
    "ADMIN": 1,
    "SUPER_ADMIN": 2,
}

# Порядок для сортировки (от lowest to highest)
ROLE_ORDER = ["USER", "ADMIN", "SUPER_ADMIN"]

# Карта разрешений для каждой роли
ROLE_PERMISSIONS = {
    "USER": {
        "entities:read": True,
        "reviews:create": True,
        "tickets:pay": True,
    },
    "ADMIN": {
        "entities:read": True,
        "reviews:create": True,
        "tickets:pay": True,
        "users:read": True,
        "users:update": True,
        "users:delete": True,
    },
    "SUPER_ADMIN": {
        "entities:read": True,
        "reviews:create": True,
        "tickets:pay": True,
        "users:read": True,
        "users:update": True,
        "users:delete": True,
        "entities:create": True,
        "entities:update": True,
        "entities:delete": True,
        "genres:create": True,
        "genres:update": True,
        "genres:delete": True,
    },
}


def get_highest_role(roles: list[str]) -> str:
    """
    Возвращает самую высокую роль из массива ролей.
    
    SUPER_ADMIN > ADMIN > USER
    """
    if not roles:
        return "USER"
    
    highest = "USER"
    for role in roles:
        role_upper = role.upper().strip()
        if role_upper in ROLE_HIERARCHY:
            if ROLE_HIERARCHY[role_upper] > ROLE_HIERARCHY[highest]:
                highest = role_upper
    return highest


def has_permission(user_roles: list[str], permission: str) -> bool:
    """
    Проверяет, есть ли у пользователя разрешение.
    
    Использует самую высокую роль для проверки прав.
    """
    highest = get_highest_role(user_roles)
    role_perms = ROLE_PERMISSIONS.get(highest, {})
    return role_perms.get(permission, False)


def get_user_permissions(user_roles: list[str]) -> dict:
    """
    Возвращает карту разрешений для пользователя на основе его самой высокой роли.
    """
    highest = get_highest_role(user_roles)
    return ROLE_PERMISSIONS.get(highest, {})


class PermissionDeniedError(Exception):
    """Исключение для отказа в доступе по роли"""
    pass


class RoleValidator:
    """Валидатор и проверщик ролей"""
    
    @staticmethod
    def validate_role(role: str) -> bool:
        """Проверяет, что роль валидна"""
        return role.upper().strip() in ROLE_HIERARCHY
    
    @staticmethod
    def get_role_level(role: str) -> int:
        """Возвращает уровень роли в иерархии"""
        return ROLE_HIERARCHY.get(role.upper().strip(), 0)
    
    @staticmethod
    def get_permissions_for_role(role: str) -> dict:
        """Возвращает карту разрешений для роли"""
        return ROLE_PERMISSIONS.get(role.upper().strip(), {})
    
    @staticmethod
    def get_all_roles() -> list[str]:
        """Возвращает список всех доступных ролей"""
        return ROLE_ORDER.copy()
    
    @staticmethod
    def check_permission(user_roles: list[str], permission: str) -> bool:
        """
        Проверяет, есть ли у пользователя нужное разрешение.
        
        Args:
            user_roles: Массив ролей пользователя
            permission: Требуемое разрешение (например, 'entities:read')
            
        Returns:
            True если разрешение есть
            
        Raises:
            PermissionDeniedError: Если разрешение отсутствует
        """
        if has_permission(user_roles, permission):
            return True
        raise PermissionDeniedError(
            f"Access denied. Required permission: '{permission}'. "
            f"Your highest role: '{get_highest_role(user_roles)}'"
        )


# Утилиты для работы с JWT токенами

# Утилиты для работы с JWT токенами

# Импортируем конфигурацию из mock_server.py
# Эти переменные будут определены при импорте mock_server
JWT_SECRET_KEY = "mock-server-secret-key-for-training-only"
JWT_ALGORITHM = "HS256"


class TokenUtils:
    """Утилиты для работы с JWT токенами"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создает JWT access токен.
        
        Args:
            data: Словарь с данными (обычно sub=user_id)
            expires_delta: Длительность жизни токена
            
        Returns:
            Закодированный JWT токен
        """
        from jose import jwt, JWTError
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создает JWT refresh токен.
        
        Args:
            data: Словарь с данными (обычно sub=user_id)
            expires_delta: Длительность жизни токена
            
        Returns:
            Закодированный JWT токен
        """
        from jose import jwt, JWTError
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(hours=1))
        to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def decode_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Декодирует и валидирует JWT токен.
        
        Args:
            token: JWT токен
            expected_type: Ожидаемый тип токена ("access" или "refresh")
            
        Returns:
            Словарь с claims если токен валиден, None если невалиден
        """
        from jose import jwt, JWTError
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != expected_type:
                return None
            return payload
        except JWTError:
            return None
