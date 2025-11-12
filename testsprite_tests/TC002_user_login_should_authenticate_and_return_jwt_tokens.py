import requests

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = "/api/v1/auth/login/"
REGISTER_ENDPOINT = "/api/v1/auth/register/"

def test_user_login_should_authenticate_and_return_jwt_tokens():
    session = requests.Session()
    headers = {"Content-Type": "application/json"}
    timeout = 30

    # First, register a new user to have valid credentials to login
    import uuid
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPass123!"

    register_payload = {
        "username": unique_username,
        "password": password,
        "email": f"{unique_username}@example.com",
        "hoTen": "Test User"
    }

    # Register the user
    try:
        reg_resp = session.post(
            f"{BASE_URL}{REGISTER_ENDPOINT}",
            json=register_payload,
            headers=headers,
            timeout=timeout
        )
        assert reg_resp.status_code == 201, f"User registration failed: {reg_resp.text}"

        # Successful login attempt with valid credentials
        login_payload = {
            "username": unique_username,
            "password": password
        }
        login_resp = session.post(
            f"{BASE_URL}{LOGIN_ENDPOINT}",
            json=login_payload,
            headers=headers,
            timeout=timeout
        )
        assert login_resp.status_code == 200, f"Login failed with status {login_resp.status_code}: {login_resp.text}"
        login_data = login_resp.json()
        assert "access" in login_data and isinstance(login_data["access"], str) and login_data["access"], "Access token missing or invalid"
        assert "refresh" in login_data and isinstance(login_data["refresh"], str) and login_data["refresh"], "Refresh token missing or invalid"

        # Failed login attempt with invalid credentials
        invalid_login_payload = {
            "username": unique_username,
            "password": "WrongPassword123!"
        }
        invalid_login_resp = session.post(
            f"{BASE_URL}{LOGIN_ENDPOINT}",
            json=invalid_login_payload,
            headers=headers,
            timeout=timeout
        )
        assert invalid_login_resp.status_code == 401, f"Invalid login did not return 401: {invalid_login_resp.text}"

    finally:
        # No user deletion endpoint provided in PRD, so cannot clean up user
        pass

test_user_login_should_authenticate_and_return_jwt_tokens()