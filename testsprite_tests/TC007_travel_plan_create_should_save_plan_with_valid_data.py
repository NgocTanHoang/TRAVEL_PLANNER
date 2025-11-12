import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_travel_plan_create_should_save_plan_with_valid_data():
    url = f"{BASE_URL}/api/v1/travel-plans/"
    headers = {
        "Content-Type": "application/json"
    }

    # Construct valid travel plan payload with required fields and some optional ones
    start_date = (date.today() + timedelta(days=10)).isoformat()
    payload = {
        "origin": "Hanoi",
        "destination": "Da Nang",
        "start_date": start_date,
        "days": 5,
        "travelers": 2,
        "travel_style": "standard",
        "budget": 1000.0,
        "rooms": 1,
        "interests": ["beach", "culture"],
        "selected_hotel": {
            "name": "Seaside Resort",
            "rating": 4.5,
            "price_per_night": 150.0
        }
    }

    response = None
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        # Assert status code 201 created
        assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
        # Assert response JSON contains confirmation keys or message
        json_resp = response.json()
        assert isinstance(json_resp, dict), "Response is not a JSON object"
        # According to PRD: just description says "Travel plan created", no schema specified
        # We expect at least a confirmation message or the created resource with an id
        assert ("message" in json_resp) or ("id" in json_resp) or ("travel_plan_id" in json_resp), \
            "Response JSON does not contain expected confirmation fields"

        # Optionally check that returned fields match the sent data partially (origin, destination)
        if "origin" in json_resp:
            assert json_resp["origin"] == payload["origin"], "Origin mismatch in response"
        if "destination" in json_resp:
            assert json_resp["destination"] == payload["destination"], "Destination mismatch in response"

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    finally:
        # If created resource ID is returned and we want to clean up, delete the travel plan
        if response and response.status_code == 201:
            json_resp = response.json()
            travel_plan_id = None
            if "id" in json_resp:
                travel_plan_id = json_resp["id"]
            elif "travel_plan_id" in json_resp:
                travel_plan_id = json_resp["travel_plan_id"]
            # Delete resource if ID found
            if travel_plan_id:
                try:
                    delete_url = f"{url}{travel_plan_id}/"
                    del_resp = requests.delete(delete_url, timeout=TIMEOUT)
                    assert del_resp.status_code in [200, 204], f"Failed to delete travel plan with ID {travel_plan_id}"
                except requests.RequestException:
                    pass


test_travel_plan_create_should_save_plan_with_valid_data()