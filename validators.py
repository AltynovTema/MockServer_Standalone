"""
Модуль для валидации данных мок-сервера.
Содержит классы для валидации сущностей и запросов.
"""

from typing import Dict, Any, Optional


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
