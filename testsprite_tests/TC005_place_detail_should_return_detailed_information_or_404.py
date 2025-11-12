import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_place_detail_returns_info_or_404():
    headers = {
        "Accept": "application/json",
    }

    # Step 1: Get a valid place ID by listing places
    places_list_url = f"{BASE_URL}/api/v1/places/"
    try:
        response = requests.get(places_list_url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        places_data = response.json()
        results = places_data.get("results", [])
        assert isinstance(results, list), "Expected 'results' to be a list"
        assert len(results) > 0, f"No places available to test with. Response: {places_data}"
        valid_place_id = None
        # Attempt to find a place with an integer maDiaDiem (the primary key field name)
        # Note: The API uses 'maDiaDiem' in response, but URL parameter is 'id'
        for place in results:
            if isinstance(place, dict):
                # Try 'maDiaDiem' first (the actual field name)
                if "maDiaDiem" in place and isinstance(place["maDiaDiem"], int):
                    valid_place_id = place["maDiaDiem"]
                    break
                # Fallback to 'id' for backward compatibility
                elif "id" in place and isinstance(place["id"], int):
                    valid_place_id = place["id"]
                    break
        # Provide more detailed error message if no valid ID found
        if valid_place_id is None:
            sample_place = results[0] if results else {}
            available_keys = list(sample_place.keys()) if isinstance(sample_place, dict) else []
            raise AssertionError(
                f"No valid place ID found in places list. "
                f"Found {len(results)} places. "
                f"Sample place keys: {available_keys}. "
                f"Expected 'maDiaDiem' or 'id' field with integer value."
            )
    except Exception as e:
        raise AssertionError(f"Failed to get a valid place ID: {e}")

    # Step 2: Test GET /api/v1/places/{id}/ for valid place ID -> should return 200 with detail
    place_detail_url = f"{BASE_URL}/api/v1/places/{valid_place_id}/"
    try:
        resp = requests.get(place_detail_url, headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected status 200 for valid place, got {resp.status_code}"
        detail = resp.json()
        assert isinstance(detail, dict), "Place detail response should be a JSON object"
        # The detail is expected to contain at least 'maDiaDiem' equal to valid_place_id
        # (API uses 'maDiaDiem' as the primary key field name)
        assert "maDiaDiem" in detail and detail["maDiaDiem"] == valid_place_id, f"Place detail ID mismatch: expected {valid_place_id}, got {detail.get('maDiaDiem', 'N/A')}"
    except Exception as e:
        raise AssertionError(f"Failed to fetch place detail for valid ID: {e}")

    # Step 3: Test GET /api/v1/places/{id}/ for a non-existent place ID -> should return 404
    # Use a very large ID unlikely to exist
    non_existent_id = 999999999
    if non_existent_id == valid_place_id:
        non_existent_id += 1
    non_exist_url = f"{BASE_URL}/api/v1/places/{non_existent_id}/"
    try:
        resp_404 = requests.get(non_exist_url, headers=headers, timeout=TIMEOUT)
        assert resp_404.status_code == 404, f"Expected status 404 for non-existent place, got {resp_404.status_code}"
    except Exception as e:
        raise AssertionError(f"Failed to get 404 for non-existent place ID: {e}")

test_place_detail_returns_info_or_404()