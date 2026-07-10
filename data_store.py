"""
Модуль для работы с хранилищем данных мок-сервера.
Поддерживает сохранение в JSON файл для персистентности.
"""

import json
import os
from datetime import datetime
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
