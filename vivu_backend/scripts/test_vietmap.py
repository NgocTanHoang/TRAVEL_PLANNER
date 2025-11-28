"""
Quick VietMap API Test
======================
"""
import sys
import os
from pathlib import Path

# Add paths
BACKEND_DIR = Path(__file__).parent / "vivu_backend"
sys.path.insert(0, str(BACKEND_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
import django
django.setup()

from django.conf import settings

def test_vietmap_api():
    print("="*80)
    print("VIETMAP API TEST")
    print("="*80)
    
    # Check API key
    api_key = getattr(settings, 'VIETMAP_API_KEY', None)
    if not api_key:
        print("\n[ERROR] VIETMAP_API_KEY not configured")
        return
    
    print(f"\n[OK] API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test VietMap tools
    try:
        from tools.vietmap_tools import get_vietmap_tools
        vietmap = get_vietmap_tools()
        print("[OK] VietMap tools loaded")
    except Exception as e:
        print(f"[ERROR] Cannot load VietMap tools: {e}")
        return
    
    # Test 1: Geocoding
    print("\n" + "-"*80)
    print("TEST 1: Geocoding")
    print("-"*80)
    
    locations = [
        "Ho Chi Minh City",
        "Da Nang",
        "Hanoi"
    ]
    
    for loc in locations:
        print(f"\nLocation: {loc}")
        try:
            result = vietmap.geocode(loc)
            if result:
                print(f"  Lat: {result.get('lat')}")
                print(f"  Lon: {result.get('lon')}")
                print(f"  Address: {result.get('formatted_address', 'N/A')}")
            else:
                print(f"  [FAIL] No result")
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    # Test 2: Distance Calculation
    print("\n" + "-"*80)
    print("TEST 2: Distance Calculation")
    print("-"*80)
    
    routes = [
        ("Ho Chi Minh City", "Da Nang"),
        ("Hanoi", "Da Nang"),
    ]
    
    for origin, dest in routes:
        print(f"\nRoute: {origin} -> {dest}")
        try:
            result = vietmap.calculate_distance_time(origin, dest, profile='car')
            if result:
                distance = result.get('distance_km', 0)
                duration = result.get('duration_minutes', 0)
                print(f"  Distance: {distance} km")
                print(f"  Duration: {duration} min")
                
                if distance == 0:
                    print(f"  [WARNING] Distance is 0 - API may have issues")
                else:
                    print(f"  [OK] Valid result")
            else:
                print(f"  [FAIL] No result")
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    # Test 3: Direct API call
    print("\n" + "-"*80)
    print("TEST 3: Direct VietMap API Call")
    print("-"*80)
    
    import requests
    
    # Test geocoding endpoint
    print("\nTesting Geocoding API:")
    try:
        url = "https://maps.vietmap.vn/api/geocode"
        params = {
            'apikey': api_key,
            'text': 'Ho Chi Minh City'
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    # Test routing endpoint
    print("\nTesting Routing API:")
    try:
        # First geocode the locations
        origin_coords = vietmap.geocode("Ho Chi Minh City")
        dest_coords = vietmap.geocode("Da Nang")
        
        if origin_coords and dest_coords:
            url = "https://maps.vietmap.vn/api/route"
            params = {
                'apikey': api_key,
                'point': f"{origin_coords['lat']},{origin_coords['lon']}",
                'point': f"{dest_coords['lat']},{dest_coords['lon']}",
                'vehicle': 'car'
            }
            response = requests.get(url, params=params, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                if 'paths' in data and len(data['paths']) > 0:
                    path = data['paths'][0]
                    distance = path.get('distance', 0) / 1000  # meters to km
                    duration = path.get('time', 0) / 60000  # ms to minutes
                    print(f"  Distance: {distance:.2f} km")
                    print(f"  Duration: {duration:.1f} min")
            else:
                print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)

if __name__ == "__main__":
    try:
        test_vietmap_api()
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
