"""
Script test Route API v3 của VietMap
"""
import os
import sys
import django
from pathlib import Path
import logging

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

# Setup logging để xem chi tiết
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.vietmap_tools import get_vietmap_tools
from tools.geo_tools import GeoTools

def test_vietmap_route_v3():
    """Test Route API v3 của VietMap"""
    print("=" * 80)
    print("TEST VIETMAP ROUTE API V3")
    print("=" * 80)
    
    # Test 1: Direct coordinates
    print("\n[Test 1] Test với tọa độ trực tiếp:")
    print("-" * 80)
    vm = get_vietmap_tools()
    
    if not vm.vietmap_api_key:
        print("❌ VIETMAP_API_KEY không được cấu hình!")
        return
    
    print(f"✅ API Key: {vm.vietmap_api_key[:10]}...")
    
    # Test với tọa độ từ tài liệu
    origin = "10.755222,106.662633"
    destination = "10.7559910,106.6633234"
    
    print(f"Origin: {origin}")
    print(f"Destination: {destination}")
    
    try:
        result = vm.calculate_distance_time(origin, destination, 'car')
        if result:
            print(f"✅ Thành công!")
            print(f"   Distance: {result.get('distance_km', 0)} km")
            print(f"   Duration: {result.get('duration_minutes', 0)} phút")
            print(f"   Distance (m): {result.get('distance_meters', 0)} m")
            print(f"   Duration (s): {result.get('duration_seconds', 0)} s")
        else:
            print("❌ Trả về None")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Với địa chỉ (cần geocode)
    print("\n[Test 2] Test với địa chỉ (cần geocode):")
    print("-" * 80)
    
    geo_tools = GeoTools()
    
    test_routes = [
        ("Hà Nội", "Hồ Chí Minh"),
        ("Cần Thơ", "Bắc Ninh"),
        ("Đà Nẵng", "Huế"),
    ]
    
    for origin_name, dest_name in test_routes:
        print(f"\nRoute: {origin_name} -> {dest_name}")
        try:
            # Geocode
            origin_coords = geo_tools.geocode(origin_name, use_vietmap=True)
            dest_coords = geo_tools.geocode(dest_name, use_vietmap=True)
            
            if not origin_coords:
                print(f"  ❌ Không thể geocode: {origin_name}")
                continue
            if not dest_coords:
                print(f"  ❌ Không thể geocode: {dest_name}")
                continue
            
            print(f"  ✅ Geocode thành công:")
            print(f"     {origin_name}: {origin_coords.get('lat')}, {origin_coords.get('lon')}")
            print(f"     {dest_name}: {dest_coords.get('lat')}, {dest_coords.get('lon')}")
            
            # Calculate route
            origin_str = f"{origin_coords['lat']},{origin_coords['lon']}"
            dest_str = f"{dest_coords['lat']},{dest_coords['lon']}"
            
            route_result = vm.calculate_distance_time(origin_str, dest_str, 'car')
            
            if route_result:
                print(f"  ✅ Route thành công:")
                print(f"     Distance: {route_result.get('distance_km', 0):.2f} km")
                print(f"     Duration: {route_result.get('duration_minutes', 0):.1f} phút")
            else:
                print(f"  ❌ Route trả về None")
                
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("HOÀN TẤT TEST")
    print("=" * 80)


if __name__ == '__main__':
    test_vietmap_route_v3()

