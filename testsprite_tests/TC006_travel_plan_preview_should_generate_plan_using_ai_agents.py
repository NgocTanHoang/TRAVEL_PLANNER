import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_travel_plan_preview_should_generate_plan_using_ai_agents():
    url = f"{BASE_URL}/api/v1/travel-plans/preview/"
    params = {
        "origin": "Hanoi",
        "destination": "Da Nang",
        "days": 5
    }
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    
    # Assert required fields in response with case-insensitive and strip match for strings
    assert data.get("origin","" ).strip().lower() == params["origin"].lower(), "Origin does not match"
    assert data.get("destination", "").strip().lower() == params["destination"].lower(), "Destination does not match"
    assert data.get("days") == params["days"], "Days does not match"
    assert isinstance(data.get("transport"), dict), "Transport should be an object"
    assert isinstance(data.get("accommodation"), dict), "Accommodation should be an object"
    assert isinstance(data.get("activities"), list), "Activities should be a list"
    assert isinstance(data.get("budget"), dict), "Budget should be an object"

test_travel_plan_preview_should_generate_plan_using_ai_agents()
