"""
Модуль для работы с хранилищем данных мок-сервера.
Поддерживает сохранение в JSON файл для персистентности.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path


class DataStore:
    """Класс для управления данными сущностей с поддержкой персистентности"""
    
    def __init__(self, storage_file: str = "data/entities.json"):
        self.storage_file = Path(storage_file)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_file()
    
    def _load_from_file(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entities = data.get("entities", {})
                    print(f"✅ Загружено {len(self.entities)} сущностей из {self.storage_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Ошибка загрузки данных: {e}. Начинаем с пустого хранилища.")
                self.entities = {}
        else:
            print("📝 Создано новое хранилище данных")
    
    def _save_to_file(self):
        try:
            data = {
                "entities": self.entities,
                "last_updated": datetime.now().isoformat(),
                "total_count": len(self.entities)
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"❌ Ошибка сохранения данных: {e}")
    
    def create(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        entity = {
            **entity_data,
            "id": entity_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.entities[entity_id] = entity
        self._save_to_file()
        return entity
    
    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self.entities.get(entity_id)
    
    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.entities.values())
    
    def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if entity_id not in self.entities:
            return None
        for key, value in update_data.items():
            if key != "id" and key != "created_at":
                self.entities[entity_id][key] = value
        self.entities[entity_id]["updated_at"] = datetime.now().isoformat()
        self._save_to_file()
        return self.entities[entity_id]
    
    def delete(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if entity_id not in self.entities:
            return None
        deleted_entity = self.entities.pop(entity_id)
        self._save_to_file()
        return deleted_entity
    
    def count(self) -> int:
        return len(self.entities)
    
    def clear(self):
        self.entities.clear()
        self._save_to_file()


class RequestHistoryStore:
    """Класс для управления историей запросов с поддержкой персистентности"""
    
    def __init__(self, storage_file: str = "data/request_history.json", max_history: int = 1000):
        self.storage_file = Path(storage_file)
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_file()
    
    def _load_from_file(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    print(f"✅ Загружено {len(self.history)} записей истории")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Ошибка загрузки истории: {e}")
                self.history = []
        else:
            print("📝 Создана новая история запросов")
    
    def _save_to_file(self):
        try:
            data = {
                "history": self.history,
                "total_requests": len(self.history),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"❌ Ошибка сохранения истории: {e}")
    
    def add(self, request_info: Dict[str, Any]):
        self.history.append(request_info)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        if len(self.history) % 10 == 0:
            self._save_to_file()
    
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.history[-limit:] if len(self.history) > limit else self.history
    
    def get_all(self) -> List[Dict[str, Any]]:
        return self.history.copy()
    
    def count(self) -> int:
        return len(self.history)
    
    def clear(self):
        self.history.clear()
        self._save_to_file()
    
    def save(self):
        self._save_to_file()


# ============================================================================
# ХРАНИЛИЩЕ ТОКЕНОВ
# ============================================================================


class TokenStore:
    """Хранилище токенов в памяти с поддержкой ротации и отзыва"""
    
    def __init__(self):
        # Ключ: token_string, Значение: dict с метаданными
        self.access_tokens: Dict[str, Dict[str, Any]] = {}
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
    
    def store_access_token(self, token: str, user_id: str, expires_at: datetime):
        """Сохраняет access токен"""
        # Сохраняем как offset-naive datetime (без timezone info) для совместимости с JWT
        expires_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
        self.access_tokens[token] = {
            "token_id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_type": "access",
            "created_at": datetime.utcnow(),
            "expires_at": expires_naive,
            "revoked": False,
        }
    
    def store_refresh_token(self, token: str, user_id: str, expires_at: datetime):
        """Сохраняет refresh токен"""
        # Сохраняем как offset-naive datetime (без timezone info) для совместимости с JWT
        expires_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
        self.refresh_tokens[token] = {
            "token_id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_type": "refresh",
            "created_at": datetime.utcnow(),
            "expires_at": expires_naive,
            "revoked": False,
        }
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет access токен.
        Возвращает метаданные если валиден, None если не найден/истёк/отозван.
        """
        token_data = self.access_tokens.get(token)
        if not token_data:
            return None
        if token_data["revoked"]:
            return None
        if datetime.utcnow() > token_data["expires_at"]:
            return None
        return token_data
    
    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет refresh токен.
        Возвращает метаданные если валиден, None если не найден/истёк/отозван.
        """
        token_data = self.refresh_tokens.get(token)
        if not token_data:
            return None
        if token_data["revoked"]:
            return None
        if datetime.utcnow() > token_data["expires_at"]:
            return None
        return token_data
    
    def revoke_token(self, token: str) -> bool:
        """Отзывает токен (любого типа). Возвращает True если токен найден и отозван."""
        # Сначала ищем в access токенах
        if token in self.access_tokens:
            self.access_tokens[token]["revoked"] = True
            return True
        # Затем в refresh токенах
        if token in self.refresh_tokens:
            self.refresh_tokens[token]["revoked"] = True
            return True
        return False
    
    def rotate_refresh_token(self, old_refresh_token: str, new_access: str, new_refresh: str, user_id: str, access_expires: datetime, refresh_expires: datetime):
        """
        Ротирует refresh токен: отзывает старый, сохраняет новый.
        """
        # Отзываем старый refresh токен
        if old_refresh_token in self.refresh_tokens:
            self.refresh_tokens[old_refresh_token]["revoked"] = True
        # Сохраняем новые токены
        self.store_access_token(new_access, user_id, access_expires)
        self.store_refresh_token(new_refresh, user_id, refresh_expires)
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о токене (любого типа) для эндпоинта валидации."""
        if token in self.access_tokens:
            data = self.access_tokens[token]
            return {
                "token_type": "access",
                "user_id": data["user_id"],
                "created_at": data["created_at"].isoformat(),
                "expires_at": data["expires_at"].isoformat(),
                "revoked": data["revoked"],
                "expired": datetime.utcnow() > data["expires_at"],
            }
        if token in self.refresh_tokens:
            data = self.refresh_tokens[token]
            return {
                "token_type": "refresh",
                "user_id": data["user_id"],
                "created_at": data["created_at"].isoformat(),
                "expires_at": data["expires_at"].isoformat(),
                "revoked": data["revoked"],
                "expired": datetime.utcnow() > data["expires_at"],
            }
        return None
    
    def count(self) -> int:
        """Общее количество активных (не отозванных) токенов."""
        active = 0
        for t in list(self.access_tokens.values()) + list(self.refresh_tokens.values()):
            if not t["revoked"]:
                active += 1
        return active
