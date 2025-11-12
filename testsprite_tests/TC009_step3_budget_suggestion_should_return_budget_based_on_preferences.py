import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_step3_budget_suggestion_should_return_budget_based_on_preferences():
    url = f"{BASE_URL}/api/v1/travel-plans/step3/"
    payload = {
        "origin": "Hanoi",
        "destination": "Da Nang",
        "days": 5,
        "travelers": 2,
        "travel_style": "standard"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    assert isinstance(data, dict), "Response JSON is not a dictionary"
    assert data, "Response JSON is empty"
    # If budget key is present, ensure it's a dictionary
    if "budget" in data:
        assert isinstance(data["budget"], dict), "Budget data is not a dictionary"


test_step3_budget_suggestion_should_return_budget_based_on_preferences()