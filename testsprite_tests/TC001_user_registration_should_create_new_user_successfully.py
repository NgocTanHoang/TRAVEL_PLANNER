import requests
import uuid

BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = f"{BASE_URL}/api/v1/auth/register/"
TIMEOUT = 30

def test_user_registration_should_create_new_user_successfully():
    # Generate a unique username to avoid conflicts
    unique_username = f"user_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": unique_username,
        "password": "StrongPass!23",
        "email": f"{unique_username}@example.com",
        "hoTen": "Test User"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(REGISTER_ENDPOINT, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to register user failed: {e}"

    assert response.status_code == 201, f"Expected status 201, got {response.status_code}"

    try:
        resp_json = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate keys in response and types
    assert "maNguoiDung" in resp_json, "Response JSON missing 'maNguoiDung'"
    assert isinstance(resp_json["maNguoiDung"], int), "'maNguoiDung' should be an integer"

    assert "tenDangNhap" in resp_json, "Response JSON missing 'tenDangNhap'"
    assert resp_json["tenDangNhap"] == unique_username, "'tenDangNhap' does not match registered username"

    assert "message" in resp_json, "Response JSON missing 'message'"
    assert isinstance(resp_json["message"], str), "'message' should be a string"
    assert resp_json["message"], "'message' should not be empty"

test_user_registration_should_create_new_user_successfully()