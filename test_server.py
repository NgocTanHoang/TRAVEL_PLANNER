"""
Test script để kiểm tra Django server đã chạy chưa
"""
import requests
import time
import sys

print("=" * 70)
print("KIỂM TRA DJANGO SERVER")
print("=" * 70)

# Đợi server khởi động
print("\nĐang đợi server khởi động...")
time.sleep(3)

# Test các endpoints
endpoints = [
    ("http://127.0.0.1:8000/", "Homepage"),
    ("http://127.0.0.1:8000/api/docs/", "API Documentation"),
    ("http://127.0.0.1:8000/api/v1/places/", "Places API"),
]

print("\n" + "=" * 70)
print("KIỂM TRA ENDPOINTS")
print("=" * 70)

for url, name in endpoints:
    try:
        response = requests.get(url, timeout=5)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name:25} - Status: {response.status_code} - {url}")
    except requests.exceptions.ConnectionError:
        print(f"✗ {name:25} - Server chưa chạy hoặc không kết nối được")
    except requests.exceptions.Timeout:
        print(f"✗ {name:25} - Timeout")
    except Exception as e:
        print(f"✗ {name:25} - Error: {type(e).__name__}")

print("\n" + "=" * 70)
print("HƯỚNG DẪN")
print("=" * 70)
print("\nNếu server đã chạy, bạn có thể:")
print("  - Trang chủ: http://127.0.0.1:8000/")
print("  - API Docs: http://127.0.0.1:8000/api/docs/")
print("  - Admin: http://127.0.0.1:8000/admin/")
print("\nNếu server chưa chạy, hãy chạy:")
print('  cd "D:\\KLTN\\MAS (1)\\MAS\\TRAVEL_PLANNER\\vivu_backend"')
print("  python manage.py runserver")

