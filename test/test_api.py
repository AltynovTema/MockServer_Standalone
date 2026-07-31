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

    def test_slow_performance_query_param(self, url_fast_api):
        """TC-014: Проверка параметра задержки"""
        path = '/entities?slow=2'
        data = {'name': 'PerformanceTest'}
        response = requests.post(url_fast_api + path, json=data)
        assert response.status_code == 201

    def test_get_entity_by_id(self, url_fast_api):
        """TC-015: Проверка получения сущности по ID"""
        create_data = {'name': 'TestEntity', 'data': {'key': 'value'}}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data)
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

    def test_update_entity(self, url_fast_api):
        """TC-018: Проверка обновления сущности"""
        create_data = {'name': 'OriginalName', 'data': {'key': 'value'}}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data)
        assert create_response.status_code == 201
        entity_id = create_response.json()['id']
        update_data = {'name': 'UpdatedName'}
        update_response = requests.put(f"{url_fast_api}/entities/{entity_id}", json=update_data)
        assert update_response.status_code == 200
        updated_entity = update_response.json()['entity']
        assert updated_entity['name'] == 'UpdatedName'

    def test_delete_entity(self, url_fast_api):
        """TC-019: Проверка удаления сущности"""
        create_data = {'name': 'ToDelete', 'data': {'key': 'value'}}
        create_response = requests.post(f"{url_fast_api}/entities", json=create_data)
        assert create_response.status_code == 201
        entity_id = create_response.json()['id']
        delete_response = requests.delete(f"{url_fast_api}/entities/{entity_id}")
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
        """TC-N004: Проверка обновления несуществующей сущности"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {'name': 'UpdatedName'}
        response = requests.put(f"{url_fast_api}/entities/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_non_existing_entity(self, url_fast_api):
        """TC-N005: Проверка удаления несуществующей сущности"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(f"{url_fast_api}/entities/{fake_id}")
        assert response.status_code == 404

    def test_delete_non_existing_booking(self, base_url):
        """TC-N006: Проверка удаления несуществующего бронирования"""
        booking_id = 999999
        response = requests.delete(f"{base_url}/{booking_id}")
        assert response.status_code == 404
