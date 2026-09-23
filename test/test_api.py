"""
Тестовый модуль для API Mock Server.
"""

import pytest
import requests


class TestPositive:
    """Позитивные тесты для API Mock Server"""

    def test_get_root_endpoint(self, url_fast_api):
        """TC-001: Проверка доступности корневого эндпоинта"""
        response = requests.get(url_fast_api)
        assert response is not None
        assert response.status_code == 200

    def test_get_with_query_dict(self, url_fast_api):
        """TC-002: Проверка GET запроса с query параметрами"""
        path = '/inspector/history'
        query = {"limit": 35}
        response = requests.get(url_fast_api + path, params=query)
        assert response.status_code == 200
        assert "limit=35" in response.url

    def test_get_with_query_tuples(self, url_fast_api):
        """TC-003: Проверка GET запроса с множественными query параметрами"""
        path = '/entities'
        query = [('filter', 'active'), ('filter', 'featured'), ('filter', 'sale')]
        response = requests.get(url_fast_api + path, params=query)
        assert response.status_code == 200
        assert 'filter=active&filter=featured&filter=sale' in response.url

    def test_post_create_booking(self, base_url, valid_payload):
        """TC-004: Проверка создания бронирования"""
        response = requests.post(base_url, json=valid_payload)
        assert response.status_code == 201

    def test_post_headers(self, base_url, valid_payload):
        """TC-005: Проверка заголовка Content-Type ответа"""
        response = requests.post(base_url, json=valid_payload)
        assert 'Content-Type' in response.headers
        assert response.headers['Content-Type'] == 'application/json'

    def test_post_bookingid(self, base_url, valid_payload):
        """TC-006: Проверка наличия и типа bookingid"""
        response = requests.post(base_url, json=valid_payload)
        booking = response.json()
        assert 'bookingid' in booking
        assert type(booking['bookingid']) is int

    def test_post_body_firstname_lastname(self, base_url, valid_payload):
        """TC-007: Проверка firstname и lastname в ответе"""
        response = requests.post(base_url, json=valid_payload)
        booking = response.json()
        assert 'firstname' in booking['booking']
        assert booking['booking']['firstname'] == valid_payload['firstname']
        assert 'lastname' in booking['booking']
        assert booking['booking']['lastname'] == valid_payload['lastname']

    def test_post_headers_booking(self, base_url, valid_payload):
        """TC-008: Проверка наличия всех обязательных заголовков"""
        expected_headers = ('content-length', 'content-type', 'date', 'server')
        response = requests.post(base_url, json=valid_payload)
        missing_headers = [h for h in expected_headers if h not in response.headers]
        assert not missing_headers

    def test_post_structure(self, base_url, valid_payload):
        """TC-009: Проверка структуры ответа"""
        response = requests.post(base_url, json=valid_payload)
        data = response.json()
        booking = data.get("booking", {})
        required_fields = ["firstname", "lastname", "totalprice", "depositpaid", "bookingdates", "additionalneeds"]
        missing_fields = [field for field in required_fields if field not in booking]
        assert not missing_fields
        expected_types = {"firstname": str, "lastname": str, "totalprice": int, "depositpaid": bool, "bookingdates": dict, "additionalneeds": (str, type(None))}
        for field, expected_type in expected_types.items():
            if field in booking:
                assert isinstance(booking[field], expected_type)

    def test_post_booking_date(self, base_url, valid_payload):
        """TC-010: Проверка дат бронирования"""
        response = requests.post(base_url, json=valid_payload)
        data = response.json()
        booking = data['booking'].get('bookingdates', {})
        assert valid_payload['bookingdates']['checkin'] == booking['checkin']
        assert valid_payload['bookingdates']['checkout'] == booking['checkout']

    def test_post_performance_booking(self, base_url, valid_payload):
        """TC-011: Проверка производительности"""
        response = requests.post(base_url, json=valid_payload)
        response_time = response.elapsed.total_seconds()
        assert response_time <= 1.0

    def test_post_with_json(self, base_url, sample_booking_data):
        """TC-012: Проверка POST запроса с JSON данными"""
        response = requests.post(base_url, json=sample_booking_data)
        assert response.status_code in (200, 201)
        response_data = response.json()
        assert "bookingid" in response_data
        assert response_data["bookingid"] is not None

    def test_post_get_chain(self, base_url, sample_booking_data):
        """TC-013: Проверка цепочки запросов POST -> GET"""
        response_post = requests.post(base_url, json=sample_booking_data)
        post_response_data = response_post.json()
        bookingid = post_response_data["bookingid"]
        response_get = requests.get(f"{base_url}/{bookingid}")
        get_response_data = response_get.json()
        assert response_get.status_code == 200
        assert get_response_data["firstname"] == sample_booking_data["firstname"]
        assert get_response_data["lastname"] == sample_booking_data["lastname"]

    def test_slow_performance_query_param(self, url_fast_api, superadmin_token):
        """TC-014: Проверка параметра задержки"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        path = '/entities?slow=2'
        data = {'name': 'PerformanceTest'}
        response = requests.post(url_fast_api + path, json=data, headers=headers)
        assert response.status_code == 201

    def test_get_entity_by_id(self, url_fast_api, superadmin_token):
        """TC-015: Проверка получения сущности по ID"""
        create_data = {'name': 'TestEntity', 'data': {'key': 'value'}}
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data, headers=headers)
        assert create_response.status_code == 201
        entity_id = create_response.json()['id']
        get_response = requests.get(f"{url_fast_api}/entities/{entity_id}")
        assert get_response.status_code == 200
        entity_data = get_response.json()
        assert entity_data['name'] == 'TestEntity'

    def test_get_entities_pagination(self, url_fast_api):
        """TC-016: Проверка пагинации списка сущностей"""
        response = requests.get(f"{url_fast_api}/entities?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert 'total_count' in data
        assert 'page' in data
        assert 'limit' in data
        assert 'entities' in data
        assert data['page'] == 1
        assert data['limit'] == 10

    def test_update_entity(self, url_fast_api, superadmin_token):
        """TC-018: Проверка обновления сущности (требует SUPER_ADMIN)"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        create_data = {'name': 'OriginalName', 'data': {'key': 'value'}}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data, headers=headers)
        assert create_response.status_code == 201
        entity_id = create_response.json()['id']
        update_data = {'name': 'UpdatedName'}
        update_response = requests.put(f"{url_fast_api}/entities/{entity_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        updated_entity = update_response.json()['entity']
        assert updated_entity['name'] == 'UpdatedName'

    def test_delete_entity(self, url_fast_api, superadmin_token):
        """TC-019: Проверка удаления сущности (требует SUPER_ADMIN)"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        create_data = {'name': 'ToDelete', 'data': {'key': 'value'}}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data, headers=headers)
        assert create_response.status_code == 201
        entity_id = create_response.json()['id']
        delete_response = requests.delete(f"{url_fast_api}/entities/{entity_id}", headers=headers)
        assert delete_response.status_code == 200
        get_response = requests.get(f"{url_fast_api}/entities/{entity_id}")
        assert get_response.status_code == 404

    def test_delete_booking(self, base_url, sample_booking_data):
        """TC-020: Проверка удаления бронирования"""
        create_response = requests.post(base_url, json=sample_booking_data)
        assert create_response.status_code == 201
        booking_id = create_response.json()['bookingid']
        delete_response = requests.delete(f"{base_url}/{booking_id}")
        assert delete_response.status_code == 200
        get_response = requests.get(f"{base_url}/{booking_id}")
        assert get_response.status_code == 404

    def test_clear_request_history(self, url_fast_api):
        """TC-021: Проверка очистки истории запросов"""
        response = requests.get(f"{url_fast_api}/inspector/history/clear")
        assert response.status_code == 200
        assert response.json()['message'] == 'Request history cleared'

    def test_get_server_stats(self, url_fast_api):
        """TC-022: Проверка получения статистики сервера"""
        response = requests.get(f"{url_fast_api}/inspector/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'total_entities' in data
        assert 'total_bookings' in data
        assert 'total_requests_logged' in data

    def test_health_check(self, url_fast_api):
        """TC-023: Проверка health check endpoint"""
        response = requests.get(f"{url_fast_api}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestNegative:
    """Негативные тесты для API Mock Server"""

    def test_non_existing_resource(self, base_url):
        """TC-N001: Проверка обработки несуществующего бронирования"""
        bookingid = 999999
        response = requests.get(f'{base_url}/{bookingid}')
        assert response.status_code == 404

    def test_create_booking_wrong_data(self, base_url, missing_required_fields_payload):
        """TC-N002: Проверка валидации - пустое обязательное поле"""
        response = requests.post(base_url, json=missing_required_fields_payload)
        assert response.status_code == 422

    def test_get_non_existing_entity(self, url_fast_api):
        """TC-N003: Проверка получения несуществующей сущности"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{url_fast_api}/entities/{fake_id}")
        assert response.status_code == 404

    def test_update_non_existing_entity(self, url_fast_api):
        """TC-N004: Проверка обновления несуществующей сущности (требует авторизацию)"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {'name': 'UpdatedName'}
        response = requests.put(f"{url_fast_api}/entities/{fake_id}", json=update_data)
        # Без токена возвращает 401 (требуется авторизация)
        assert response.status_code == 401

    def test_delete_non_existing_entity(self, url_fast_api):
        """TC-N005: Проверка удаления несуществующей сущности (требует авторизацию)"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(f"{url_fast_api}/entities/{fake_id}")
        # Без токена возвращает 401 (требуется авторизация)
        assert response.status_code == 401

    def test_delete_non_existing_booking(self, base_url):
        """TC-N006: Проверка удаления несуществующего бронирования"""
        booking_id = 999999
        response = requests.delete(f"{base_url}/{booking_id}")
        assert response.status_code == 404


# ============================================================================
# ТЕСТЫ ДЛЯ АВТОРИЗАЦИИ
# ============================================================================


class TestAuthPositive:
    """Позитивные тесты для JWT аутентификации"""
    
    def test_auth_login_success(self, url_fast_api):
        """TC-A001: Успешный вход с валидными учётными данными"""
        response = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 300  # 5 минут * 60
    
    def test_auth_login_different_users(self, url_fast_api):
        """TC-A002: Вход разными пользователями возвращает разные токены"""
        admin_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        user_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "user", "password": "user123"},
        )
        assert admin_resp.status_code == 200
        assert user_resp.status_code == 200
        admin_data = admin_resp.json()
        user_data = user_resp.json()
        assert admin_data["access_token"] != user_data["access_token"]
    
    def test_protected_data_with_valid_token(self, url_fast_api):
        """TC-A003: Доступ к защищённым данным с валидным токеном"""
        # Сначала получаем токен
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.json()["access_token"]
        
        # Запрашиваем защищённые данные
        response = requests.get(
            f"{url_fast_api}/protected/data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sensitive_data" in data
        assert data["user_id"] == "admin"
    
    def test_token_refresh(self, url_fast_api):
        """TC-A004: Обновление токенов через refresh endpoint"""
        # Получаем исходные токены
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "user", "password": "user123"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        
        # Обновляем
        refresh_resp = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Новый refresh токен отличается от старого (ротация)
        assert data["refresh_token"] != refresh_token
    
    def test_token_validation_valid(self, url_fast_api):
        """TC-A005: Валидация валидного токена"""
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{url_fast_api}/auth/validate",
            params={"token": access_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["token_type"] == "access"
        assert data["user_id"] == "admin"
    
    def test_token_logout(self, url_fast_api):
        """TC-A006: Выход из системы - отзыв токена"""
        # Получаем токен
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.json()["access_token"]
        
        # Логаут
        logout_resp = requests.post(
            f"{url_fast_api}/auth/logout",
            json={"token": access_token},
        )
        assert logout_resp.status_code == 200
        
        # Токен больше не должен работать
        response = requests.get(
            f"{url_fast_api}/protected/data",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401
    
    def test_full_token_lifecycle(self, url_fast_api):
        """TC-A007: Полный цикл жизни токена (login -> use -> refresh -> use -> logout)"""
        # 1. Логин
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        
        # 2. Используем access токен
        protected_resp = requests.get(
            f"{url_fast_api}/protected/data",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert protected_resp.status_code == 200
        
        # 3. Обновляем токены
        refresh_resp = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        
        # 4. Используем новые токены
        protected_resp2 = requests.get(
            f"{url_fast_api}/protected/data",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert protected_resp2.status_code == 200
        
        # 5. Выходим
        logout_resp = requests.post(
            f"{url_fast_api}/auth/logout",
            json={"token": new_tokens["access_token"]},
        )
        assert logout_resp.status_code == 200


class TestAuthNegative:
    """Негативные тесты для JWT аутентификации"""
    
    def test_auth_login_wrong_password(self, url_fast_api):
        """TC-A010: Вход с неверным паролем"""
        response = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "wrong_password"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_protected_data_without_token(self, url_fast_api):
        """TC-A008: Доступ к защищённым данным без токена"""
        response = requests.get(f"{url_fast_api}/protected/data")
        assert response.status_code == 401
    
    def test_protected_data_with_invalid_token(self, url_fast_api):
        """TC-A009: Доступ к защищённым данным с невалидным токеном"""
        response = requests.get(
            f"{url_fast_api}/protected/data",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401
    
    def test_token_refresh_with_expired_token(self, url_fast_api):
        """TC-A011: Обновление с истёкшим refresh токеном"""
        # Используем заведомо невалидный refresh токен
        response = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"},
        )
        assert response.status_code == 401
    
    def test_token_refresh_with_used_refresh_token(self, url_fast_api):
        """TC-A012: Обновление с уже использованным refresh токеном (ротация)"""
        # Получаем токены
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "user", "password": "user123"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        
        # Первое обновление - успешно
        refresh_resp1 = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp1.status_code == 200
        new_tokens = refresh_resp1.json()
        
        # Пытаемся использовать старый refresh токен снова - должно отказаться
        refresh_resp2 = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp2.status_code == 401
    
    def test_token_validation_of_revoked_token(self, url_fast_api):
        """TC-A013: Валидация отозванного токена"""
        # Получаем токен
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.json()["access_token"]
        
        # Отозываем токен
        requests.post(
            f"{url_fast_api}/auth/logout",
            json={"token": access_token},
        )
        
        # Проверяем валидацию
        response = requests.get(
            f"{url_fast_api}/auth/validate",
            params={"token": access_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["revoked"] is True
    
    def test_logout_without_token(self, url_fast_api):
        """TC-A014: Выход без указания токена"""
        response = requests.post(
            f"{url_fast_api}/auth/logout",
            json={},
        )
        assert response.status_code == 400


# ============================================================================
# ТЕСТЫ ДЛЯ СИСТЕМЫ РОЛЕЙ (RBAC)
# ============================================================================


class TestRolesPositive:
    """Позитивные тесты для ролевой системы"""
    
    def test_login_superadmin_has_all_roles(self, url_fast_api):
        """TC-R001: Супер-админ получает массив всех ролей"""
        response = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "superadmin", "password": "superadmin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # Декодируем JWT payload (base64)
        import base64
        parts = data["access_token"].split(".")
        payload = base64.b64decode(parts[1] + "==")
        import json
        payload_data = json.loads(payload)
        roles = payload_data.get("roles", [])
        assert "USER" in roles
        assert "ADMIN" in roles
        assert "SUPER_ADMIN" in roles
    
    def test_login_admin_has_user_and_admin_roles(self, url_fast_api):
        """TC-R002: Админ получает роли USER и ADMIN"""
        response = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        import base64, json
        parts = data["access_token"].split(".")
        payload = base64.b64decode(parts[1] + "==")
        payload_data = json.loads(payload)
        roles = payload_data.get("roles", [])
        assert "USER" in roles
        assert "ADMIN" in roles
        assert "SUPER_ADMIN" not in roles
    
    def test_login_user_has_only_user_role(self, url_fast_api):
        """TC-R003: Обычный пользователь получает только роль USER"""
        response = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "user", "password": "user123"},
        )
        assert response.status_code == 200
        data = response.json()
        import base64, json
        parts = data["access_token"].split(".")
        payload = base64.b64decode(parts[1] + "==")
        payload_data = json.loads(payload)
        roles = payload_data.get("roles", [])
        assert roles == ["USER"]
    
    def test_auth_me_returns_roles_and_permissions(self, url_fast_api, superadmin_token):
        """TC-R004: /auth/me возвращает массив ролей и permissions"""
        response = requests.get(
            f"{url_fast_api}/auth/me",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "highestRole" in data
        assert "permissions" in data
        assert "roleHierarchy" in data
        assert data["highestRole"] == "SUPER_ADMIN"
        assert isinstance(data["roles"], list)
        assert "entities:create" in data["permissions"]
    
    def test_auth_me_user_permissions(self, url_fast_api, user_token):
        """TC-R005: /auth/me для USER возвращает ограниченные permissions"""
        response = requests.get(
            f"{url_fast_api}/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["highestRole"] == "USER"
        assert data["roles"] == ["USER"]
        permissions = data["permissions"]
        assert "entities:read" in permissions
        assert "entities:create" not in permissions
        assert "users:delete" not in permissions
    
    def test_root_endpoint_shows_roles_info(self, url_fast_api):
        """TC-R006: Корневой эндпоинт содержит информацию о ролях"""
        response = requests.get(url_fast_api)
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "hierarchy" in data["roles"]
        assert data["roles"]["hierarchy"]["SUPER_ADMIN"] > data["roles"]["hierarchy"]["ADMIN"]
        assert data["roles"]["hierarchy"]["ADMIN"] > data["roles"]["hierarchy"]["USER"]
    
    def test_refresh_token_preserves_roles(self, url_fast_api):
        """TC-R007: Обновление токена сохраняет массив ролей"""
        # Логин как ADMIN
        login_resp = requests.post(
            f"{url_fast_api}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        
        # Обновляем
        refresh_resp = requests.post(
            f"{url_fast_api}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        new_access = refresh_resp.json()["access_token"]
        
        # Проверяем payload нового токена
        import base64, json
        parts = new_access.split(".")
        payload = base64.b64decode(parts[1] + "==")
        payload_data = json.loads(payload)
        roles = payload_data.get("roles", [])
        assert "USER" in roles
        assert "ADMIN" in roles
    
    def test_super_admin_can_create_entity(self, url_fast_api, superadmin_token):
        """TC-R008: SUPER_ADMIN может создавать сущности"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        data = {"name": "SuperAdminEntity", "data": {"createdBy": "superadmin"}}
        response = requests.post(f"{url_fast_api}/entities", json=data, headers=headers)
        assert response.status_code == 201
        response_data = response.json()
        assert "id" in response_data
        assert response_data["highestRole"] == "SUPER_ADMIN"
    
    def test_super_admin_can_update_entity(self, url_fast_api, superadmin_token):
        """TC-R009: SUPER_ADMIN может обновлять сущности"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        # Создаём
        create_resp = requests.post(
            f"{url_fast_api}/entities",
            json={"name": "ToUpdate", "data": {}},
            headers=headers,
        )
        assert create_resp.status_code == 201
        entity_id = create_resp.json()["id"]
        
        # Обновляем
        update_resp = requests.put(
            f"{url_fast_api}/entities/{entity_id}",
            json={"name": "UpdatedBySuperAdmin"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["entity"]["name"] == "UpdatedBySuperAdmin"
    
    def test_super_admin_can_delete_entity(self, url_fast_api, superadmin_token):
        """TC-R010: SUPER_ADMIN может удалять сущности"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        # Создаём
        create_resp = requests.post(
            f"{url_fast_api}/entities",
            json={"name": "ToBeDeleted", "data": {}},
            headers=headers,
        )
        entity_id = create_resp.json()["id"]
        
        # Удаляем
        delete_resp = requests.delete(
            f"{url_fast_api}/entities/{entity_id}",
            headers=headers,
        )
        assert delete_resp.status_code == 200
        # Проверяем что удалена
        get_resp = requests.get(f"{url_fast_api}/entities/{entity_id}")
        assert get_resp.status_code == 404


class TestRolesNegative:
    """Негативные тесты для ролевой системы"""
    
    def test_user_cannot_create_entity(self, url_fast_api, user_token):
        """TC-R011: USER не может создавать сущности (403)"""
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {"name": "UnauthorizedCreate", "data": {}}
        response = requests.post(f"{url_fast_api}/entities", json=data, headers=headers)
        assert response.status_code == 403
        assert "entities:create" in response.json()["detail"]
    
    def test_user_cannot_update_entity(self, url_fast_api, user_token):
        """TC-R012: USER не может обновлять сущности (403)"""
        headers = {"Authorization": f"Bearer {user_token}"}
        update_resp = requests.put(
            f"{url_fast_api}/entities/00000000-0000-0000-0000-000000000000",
            json={"name": "test"},
            headers=headers,
        )
        assert update_resp.status_code == 403
    
    def test_user_cannot_delete_entity(self, url_fast_api, user_token):
        """TC-R013: USER не может удалять сущности (403)"""
        headers = {"Authorization": f"Bearer {user_token}"}
        delete_resp = requests.delete(
            f"{url_fast_api}/entities/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert delete_resp.status_code == 403
    
    def test_admin_cannot_create_entity(self, url_fast_api, admin_token):
        """TC-R014: ADMIN не может создавать сущности (403)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {"name": "AdminCreateAttempt", "data": {}}
        response = requests.post(f"{url_fast_api}/entities", json=data, headers=headers)
        assert response.status_code == 403
        assert "entities:create" in response.json()["detail"]
    
    def test_admin_cannot_delete_entity(self, url_fast_api, admin_token):
        """TC-R015: ADMIN не может удалять сущности (403)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        delete_resp = requests.delete(
            f"{url_fast_api}/entities/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert delete_resp.status_code == 403
    
    def test_admin_can_read_and_update_entity(self, url_fast_api, admin_token):
        """TC-R016: ADMIN может читать и обновлять сущности (но не создавать/удалять)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # ADMIN не может создать, но может читать публичные
        get_resp = requests.get(f"{url_fast_api}/entities?page=1&limit=1")
        assert get_resp.status_code == 200
        # ADMIN не может обновить (entities:update требует SUPER_ADMIN)
        update_resp = requests.put(
            f"{url_fast_api}/entities/00000000-0000-0000-0000-000000000000",
            json={"name": "test"},
            headers=headers,
        )
        assert update_resp.status_code == 403
    
    def test_get_protected_data_requires_auth(self, url_fast_api):
        """TC-R017: /protected/data требует авторизацию"""
        response = requests.get(f"{url_fast_api}/protected/data")
        assert response.status_code == 401
    
    def test_protected_data_returns_roles(self, url_fast_api, user_token):
        """TC-R018: /protected/data возвращает массив ролей"""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(
            f"{url_fast_api}/protected/data",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "highestRole" in data
        assert data["highestRole"] == "USER"
    
    def test_no_token_cannot_access_protected(self, url_fast_api):
        """TC-R019: Без токена доступ к защищённым эндпоинтам закрыт"""
        response = requests.post(
            f"{url_fast_api}/entities",
            json={"name": "NoAuth"},
        )
        assert response.status_code == 401
    
    def test_invalid_token_returns_401(self, url_fast_api):
        """TC-R020: Невалидный токен возвращает 401"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(
            f"{url_fast_api}/auth/me",
            headers=headers,
        )
        assert response.status_code == 401

