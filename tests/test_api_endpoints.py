import pytest
import requests
import json


# ============================================================================
# ФИКСТУРЫ
# ============================================================================

@pytest.fixture(scope="function")
def url_fast_api(request):
    """Возвращает URL для FastAPI сервера"""
    URL = 'http://127.0.0.1:8000'
    print(f"\n\t[ФИКСТУРА] URL: {URL} передан в '{request.node.name}' ✅")
    return URL


@pytest.fixture(scope="function")
def booking_api_url(request):
    """Возвращает URL для API бронирования"""
    URL = 'http://127.0.0.1:8000/booking'
    print(f"\n\t[ФИКСТУРА] URL: {URL} передан в '{request.node.name}' ✅")
    return URL


@pytest.fixture(scope="function")
def sample_booking_data(request):
    """Возвращает стандартные данные для бронирования"""
    data = {
        'firstname': 'Artem',
        'lastname': 'Altynov',
        'totalprice': 15000,
        'depositpaid': True,
        'bookingdates': {'checkin': '2026-08-06', 'checkout': '2026-08-10'},
        'additionalneeds': 'Breakfast'
    }
    print(f"\n\t[ФИКСТУРА] Параметры бронирования переданы в '{request.node.name}' ✅")
    return data


@pytest.fixture
def sample_banck_account_data(request):
    """Возвращает данные банковского счета"""
    data = {
        "bank": "T-bank",
        "account_number": 1234567890,
        "balance": 300,
        "is_active": True
    }
    print(f"[ФИКСТУРА] Данные банковского счета переданы в {request.node.name} ✅")
    return data


# ============================================================================
# ТЕСТЫ
# ============================================================================

def test_get_root_endpoint(url_fast_api):
    """Тест проверяет доступность корневого эндпоинта:
    
    1. Отправляет GET-запрос на корневой эндпоинт (/) мок-сервера
    2. Проверяет, что response object не None
    3. Проверяет, что статус код равен 200
    """
    response = requests.get(url_fast_api)
    assert response is not None
    assert response.status_code == 200


def test_get_with_query_dict(url_fast_api):
    """Тест проверяет GET-запрос с query-параметрами:
    
    1. Отправляет GET-запрос к /inspector/history с параметром limit=35
    2. Проверяет, что статус код равен 200
    3. Проверяет, что параметры действительно попали в URL
    """
    path = '/inspector/history'
    query = {"limit": 35}
    response = requests.get(url_fast_api + path, params=query)
    assert response.status_code == 200
    assert "limit=35" in response.url


def test_get_with_query_tuples(url_fast_api):
    """Тест проверяет GET-запрос с query-параметрами в виде списка кортежей:
    
    1. Отправляет GET-запрос к /entities с фильтрами
    2. Проверяет, что статус код равен 200
    3. Проверяет, что все три параметра присутствуют в URL
    """
    path = '/entities'
    query = [('filter', 'active'), ('filter', 'featured'), ('filter', 'sale')]
    response = requests.get(url_fast_api + path, params=query)
    assert response.status_code == 200
    assert 'filter=active&filter=featured&filter=sale' in response.url


def test_post_with_json(booking_api_url, sample_booking_data):
    """Тест проверяет POST-запрос с JSON данными:
    
    1. Отправляет POST-запрос с данными бронирования
    2. Проверяет, что статус код равен 200 или 201
    3. Проверяет, что ответ содержит ключ "bookingid"
    4. Проверяет, что bookingid не None
    """
    response = requests.post(booking_api_url, json=sample_booking_data)
    assert response.status_code in (200, 201)
    
    response_data = response.json()
    assert "bookingid" in response_data
    assert response_data["bookingid"] is not None


def test_post_get_chain(booking_api_url, sample_booking_data):
    """Тест проверяет цепочку запросов - POST затем GET:
    
    1. Создает бронирование через POST-запрос
    2. Получает ID бронирования из ответа
    3. Отправляет GET-запрос для получения данных
    4. Проверяет, что данные из GET совпадают с отправленными через POST
    """
    # Создаем бронирование
    response_post = requests.post(booking_api_url, json=sample_booking_data)
    post_response_data = response_post.json()
    bookingid = post_response_data["bookingid"]
    
    # Получаем данные о бронировании
    response_get = requests.get(f"{booking_api_url}/{bookingid}")
    get_response_data = response_get.json()
    
    # Проверяем соответствие данных
    assert response_get.status_code == 200
    assert get_response_data["firstname"] == sample_booking_data["firstname"]
    assert get_response_data["lastname"] == sample_booking_data["lastname"]


def test_json_vs_data_params(url_fast_api, sample_banck_account_data):
    """Тест проверяет разницу между json= и data= параметрами:
    
    1. Отправляет POST-запрос с использованием json=sample_banck_account_data
    2. Отправляет POST-запрос с использованием data=sample_banck_account_data
    3. Проверяет, что статус код равен 201 для обоих запросов
    4. Проверяет, что Content-Type заголовки различаются
    """
    # Тест json= параметр
    response_json = requests.post(f"{url_fast_api}/entities", json=sample_banck_account_data)
    assert response_json.status_code == 201
    
    # Тест data= параметр
    response_data = requests.post(f"{url_fast_api}/entities", data=sample_banck_account_data)
    assert response_data.status_code == 201
    
    # Получаем Content-Type заголовки
    content_type_json = response_json.request.headers.get('Content-Type')
    content_type_data = response_data.request.headers.get('Content-Type')
    
    # Проверяем, что Content-Type разные
    assert 'application/json' in content_type_json
    assert 'application/x-www-form-urlencoded' in content_type_data
    assert content_type_json != content_type_data


def test_post_with_custom_headers(url_fast_api):
    """Тест проверяет работу с заголовками:
    
    1. Создает заголовки Authorization и X-Custom-Header
    2. Отправляет GET-запрос с этими заголовками
    3. Проверяет, что статус код равен 200
    4. Проверяет, что заголовки были отправлены
    """
    path = '/inspector/history'
    headers = {
        "Authorization": "Bearer token123",
        "X-Custom-Header": "MyValue"
    }
    
    response = requests.get(f'{url_fast_api}/{path}', headers=headers)
    assert response.status_code == 200
    assert "X-Custom-Header" in response.request.headers and headers["Authorization"] in response.request.headers["Authorization"]


def test_non_existing_resource(booking_api_url):
    """Тест проверяет обработку несуществующих ресурсов:
    
    1. Отправляет GET-запрос на несуществующее бронирование (ID 999999)
    2. Проверяет, что статус код равен 404 (Not Found)
    """
    bookingid = 999999
    response = requests.get(f'{booking_api_url}/{bookingid}')
    assert response.status_code == 404


