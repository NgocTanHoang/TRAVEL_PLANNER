import requests

BASE_URL = "http://localhost:8000"
STEP1_ENDPOINT = "/api/v1/travel-plans/step1/"
TIMEOUT = 30

def test_step1_location_selection_should_validate_locations_and_return_distance():
    url = BASE_URL + STEP1_ENDPOINT
    headers = {
        "Content-Type": "application/json"
    }
    # Example valid origin and destination locations
    payload = {
        "origin": "Hanoi",
        "destination": "Ho Chi Minh City"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "origin" in data, "'origin' field missing in response"
    assert isinstance(data["origin"], dict), "'origin' should be an object"

    assert "destination" in data, "'destination' field missing in response"
    assert isinstance(data["destination"], dict), "'destination' should be an object"

    assert "distance_km" in data, "'distance_km' field missing in response"
    assert isinstance(data["distance_km"], (int, float)), "'distance_km' should be a number"
    assert data["distance_km"] > 0, "'distance_km' should be positive"

    assert "estimated_duration" in data, "'estimated_duration' field missing in response"
    assert isinstance(data["estimated_duration"], str), "'estimated_duration' should be a string"
    assert data["estimated_duration"], "'estimated_duration' should not be empty"

    assert "recommended_transport" in data, "'recommended_transport' field missing in response"
    assert isinstance(data["recommended_transport"], str), "'recommended_transport' should be a string"
    assert data["recommended_transport"], "'recommended_transport' should not be empty"

test_step1_location_selection_should_validate_locations_and_return_distance()