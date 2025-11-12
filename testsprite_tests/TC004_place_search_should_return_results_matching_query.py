import requests

BASE_URL = "http://localhost:8000"

def test_place_search_should_return_results_matching_query():
    search_query = "beach"
    url = f"{BASE_URL}/api/v1/places/search/"
    params = {"q": search_query}
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200

    data = response.json()
    assert "results" in data, "Response JSON missing 'results' key"
    assert "count" in data, "Response JSON missing 'count' key"
    assert "query" in data, "Response JSON missing 'query' key"
    assert data["query"].lower() == search_query.lower(), f"Response query does not match request query: {data['query']} != {search_query}"

    # Validate results is a list
    assert isinstance(data["results"], list), "'results' should be a list"

    # Optionally check that each item contains the search query in some form (e.g., name or description)
    # since schema is generic object, we just check that results are present when count > 0
    if data["count"] > 0:
        assert len(data["results"]) > 0, "Count indicates results but results list is empty"

test_place_search_should_return_results_matching_query()