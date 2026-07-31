import pytest


@pytest.fixture(scope="module")
def base_url(request):
    url = "http://127.0.0.1:8000/booking"
    return url


@pytest.fixture(scope="module")
def url_fast_api(request):
    url = "http://127.0.0.1:8000"
    return url


@pytest.fixture
def valid_payload(request):
    VALID_PAYLOAD = {
        "firstname": "Jim",
        "lastname": "Brown",
        "totalprice": 10000,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-08-06",
            "checkout": "2026-08-10"
        },
        "additionalneeds": "Breakfast"
    }
    return VALID_PAYLOAD


@pytest.fixture
def sample_booking_data(request):
    data = {
        'firstname': 'Artem',
        'lastname': 'Altynov',
        'totalprice': 15000,
        'depositpaid': True,
        'bookingdates': {'checkin': '2026-08-06', 'checkout': '2026-08-10'},
        'additionalneeds': 'Breakfast'
    }
    return data


@pytest.fixture
def missing_required_fields_payload(request):
    MISSING_REQUIRED_FIELDS_PAYLOAD = {
        "firstname": "",
        "lastname": "Алтынов",
        "totalprice": 10000,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-08-06",
            "checkout": "2026-08-10"
        },
        "additionalneeds": "Завтрак, Обед, Ужин"
    }
    return MISSING_REQUIRED_FIELDS_PAYLOAD


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук для расширенного вывода при запуске с -v"""
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and item.config.getoption('verbose') >= 1:
        test_name = item.name
        test_doc = item.obj.__doc__ if item.obj and item.obj.__doc__ else ""
        
        if test_doc:
            print(f"\n  📋 {test_doc.strip()}")
        
        if report.passed:
            print(f"  ✅ {test_name} - PASSED")
        elif report.failed:
            print(f"  ❌ {test_name} - FAILED")
        elif report.skipped:
            print(f"  ⏭️  {test_name} - SKIPPED")
