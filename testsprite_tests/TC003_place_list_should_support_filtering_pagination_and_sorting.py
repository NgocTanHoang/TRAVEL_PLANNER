import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_place_list_filtering_pagination_sorting():
    url = f"{BASE_URL}/api/v1/places/"
    headers = {
        "Accept": "application/json"
    }
    # Define query parameters for filtering, pagination, and sorting
    params = {
        "search": "beach",
        "city": "Da Nang",
        "category": "nature",
        "limit": 5,
        "ordering": "-name"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    # Check status code
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    # Validate response content type
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type, f"Expected 'application/json' content type, got '{content_type}'"

    data = response.json()

    # Validate presence of keys 'count' and 'results'
    assert "count" in data, "'count' key missing in response"
    assert "results" in data, "'results' key missing in response"

    # Validate 'results' is a list
    results = data["results"]
    assert isinstance(results, list), "'results' is not a list"

    # Validate pagination limit respected (results count <= limit)
    assert len(results) <= params["limit"], f"Number of results ({len(results)}) exceeds limit ({params['limit']})"

    # Validate filtering: Each result should match search, city, and category filters if those fields are available
    # Because schema of objects is not fully specified, do best effort
    for place in results:
        # Check name for search keyword presence (case insensitive)
        if "search" in params and params["search"]:
            name_match = False
            if "name" in place and isinstance(place["name"], str):
                if params["search"].lower() in place["name"].lower():
                    name_match = True
            assert name_match, f"Search keyword '{params['search']}' not found in place name '{place.get('name')}'"

        # Check city match if city field exists
        if "city" in params and params["city"]:
            city_match = False
            if "city" in place and isinstance(place["city"], str):
                if params["city"].lower() == place["city"].lower():
                    city_match = True
            assert city_match, f"City filter '{params['city']}' does not match place city '{place.get('city')}'"

        # Check category match if category field exists
        if "category" in params and params["category"]:
            category_match = False
            if "category" in place and isinstance(place["category"], str):
                if params["category"].lower() == place["category"].lower():
                    category_match = True
            assert category_match, f"Category filter '{params['category']}' does not match place category '{place.get('category')}'"

    # Validate sorting: results should be ordered descending by 'name'
    # Extract names safely
    names = [place.get("name", "") for place in results]
    sorted_names = sorted(names, reverse=True)
    assert names == sorted_names, "Results are not sorted descending by 'name' as expected"

test_place_list_filtering_pagination_sorting()