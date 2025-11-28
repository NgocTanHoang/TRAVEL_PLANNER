"""
Test geocode Huế với VietMap
"""
import os
import sys
import django
from pathlib import Path
import logging
import requests

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.vietmap_tools import get_vietmap_tools

def test_geocode_hue():
    """Test geocode Huế"""
    print("=" * 80)
    print("TEST GEOCODE HUẾ")
    print("=" * 80)
    
    vm = get_vietmap_tools()
    
    if not vm.vietmap_api_key:
        print("❌ VIETMAP_API_KEY không được cấu hình!")
        return
    
    print(f"✅ API Key: {vm.vietmap_api_key[:10]}...")
    
    # Test 1: migrate-address/v3
    print("\n[Test 1] Test /migrate-address/v3:")
    print("-" * 80)
    try:
        url = f"{vm.base_url}/migrate-address/v3"
        params = {
            'apikey': vm.vietmap_api_key,
            'text': 'Huế'
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            boundaries = data.get('boundaries', [])
            print(f"Boundaries count: {len(boundaries)}")
            for i, boundary in enumerate(boundaries):
                print(f"  Boundary {i}: type={boundary.get('type')}, name={boundary.get('name')}, full_name={boundary.get('full_name')}")
                print(f"    Has geometry: {bool(boundary.get('geometry'))}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: search endpoint
    print("\n[Test 2] Test /search:")
    print("-" * 80)
    try:
        url = f"{vm.base_url}/search"
        params = {
            'apikey': vm.vietmap_api_key,
            'text': 'Huế',
            'limit': 5
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
                if data.get('code') == 'OK':
                    data_obj = data.get('data', {})
                    if isinstance(data_obj, dict):
                        features = data_obj.get('features', [])
                        print(f"Features count: {len(features)}")
                        for i, feature in enumerate(features[:3]):
                            props = feature.get('properties', {})
                            geometry = feature.get('geometry', {})
                            coords = geometry.get('coordinates', [])
                            print(f"  Feature {i}: name={props.get('name')}, region={props.get('region')}")
                            print(f"    Coordinates: {coords}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: geocode function
    print("\n[Test 3] Test geocode function:")
    print("-" * 80)
    try:
        result = vm.geocode('Huế')
        if result:
            print(f"✅ Thành công!")
            print(f"   Lat: {result.get('lat')}")
            print(f"   Lon: {result.get('lon')}")
            print(f"   Address: {result.get('formatted_address')}")
        else:
            print("❌ Trả về None")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_geocode_hue()

