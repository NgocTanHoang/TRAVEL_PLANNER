import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_analytics_should_return_aggregate_data():
    url = f"{BASE_URL}/api/v1/analytics/"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"Request to analytics endpoint failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    assert isinstance(data, dict), "Response JSON is not an object/dict"
    for key in ["total_places", "total_users", "total_itineraries"]:
        assert key in data, f"Key '{key}' missing from response"
        assert isinstance(data[key], int), f"Value for '{key}' is not an integer"

test_analytics_should_return_aggregate_data()