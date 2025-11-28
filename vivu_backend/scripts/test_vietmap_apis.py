"""
Test các API của VietMap - chạy 3 lần để kiểm tra tính ổn định
"""
import os
import sys
import django
from pathlib import Path
import logging
import time

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.vietmap_tools import get_vietmap_tools
from tools.geo_tools import GeoTools

def test_geocoding(vm, test_locations):
    """Test geocoding API"""
    print("\n" + "=" * 80)
    print("TEST GEOCODING API")
    print("=" * 80)
    
    results = {}
    for location in test_locations:
        print(f"\n📍 Geocoding: {location}")
        try:
            result = vm.geocode(location)
            if result:
                results[location] = {
                    'success': True,
                    'lat': result.get('lat'),
                    'lon': result.get('lon'),
                    'address': result.get('formatted_address', '')[:50]
                }
                print(f"  ✅ Thành công: {result.get('lat')}, {result.get('lon')}")
                print(f"     Address: {result.get('formatted_address', '')[:80]}")
            else:
                results[location] = {'success': False, 'error': 'Returned None'}
                print(f"  ❌ Trả về None")
        except Exception as e:
            results[location] = {'success': False, 'error': str(e)}
            print(f"  ❌ Lỗi: {e}")
    
    return results

def test_routing(vm, test_routes):
    """Test routing API"""
    print("\n" + "=" * 80)
    print("TEST ROUTING API (calculate_distance_time)")
    print("=" * 80)
    
    results = {}
    for origin, destination in test_routes:
        route_name = f"{origin} -> {destination}"
        print(f"\n🛣️  Route: {route_name}")
        try:
            result = vm.calculate_distance_time(origin, destination, 'car')
            if result:
                results[route_name] = {
                    'success': True,
                    'distance_km': result.get('distance_km'),
                    'duration_minutes': result.get('duration_minutes')
                }
                print(f"  ✅ Thành công:")
                print(f"     Distance: {result.get('distance_km', 0):.2f} km")
                print(f"     Duration: {result.get('duration_minutes', 0):.1f} phút")
            else:
                results[route_name] = {'success': False, 'error': 'Returned None'}
                print(f"  ❌ Trả về None")
        except Exception as e:
            results[route_name] = {'success': False, 'error': str(e)}
            print(f"  ❌ Lỗi: {e}")
    
    return results

def test_geocode_with_addresses(geo_tools, test_locations):
    """Test geocoding với địa chỉ (sử dụng GeoTools)"""
    print("\n" + "=" * 80)
    print("TEST GEOCODING VỚI ĐỊA CHỈ (GeoTools)")
    print("=" * 80)
    
    results = {}
    for location in test_locations:
        print(f"\n📍 Geocoding: {location}")
        try:
            result = geo_tools.geocode(location, use_vietmap=True)
            if result:
                results[location] = {
                    'success': True,
                    'lat': result.get('lat'),
                    'lon': result.get('lon'),
                    'address': result.get('formatted_address', '')[:50]
                }
                print(f"  ✅ Thành công: {result.get('lat')}, {result.get('lon')}")
                print(f"     Address: {result.get('formatted_address', '')[:80]}")
            else:
                results[location] = {'success': False, 'error': 'Returned None'}
                print(f"  ❌ Trả về None")
        except Exception as e:
            results[location] = {'success': False, 'error': str(e)}
            print(f"  ❌ Lỗi: {e}")
    
    return results

def test_routing_with_addresses(geo_tools, test_routes):
    """Test routing với địa chỉ (sử dụng GeoTools)"""
    print("\n" + "=" * 80)
    print("TEST ROUTING VỚI ĐỊA CHỈ (GeoTools)")
    print("=" * 80)
    
    results = {}
    for origin, destination in test_routes:
        route_name = f"{origin} -> {destination}"
        print(f"\n🛣️  Route: {route_name}")
        try:
            result = geo_tools.calculate_distance_time(origin, destination, profile='driving-car', use_vietmap=True)
            if result:
                results[route_name] = {
                    'success': True,
                    'distance_km': result.get('distance_km'),
                    'duration_minutes': result.get('duration_minutes')
                }
                print(f"  ✅ Thành công:")
                print(f"     Distance: {result.get('distance_km', 0):.2f} km")
                print(f"     Duration: {result.get('duration_minutes', 0):.1f} phút")
            else:
                results[route_name] = {'success': False, 'error': 'Returned None'}
                print(f"  ❌ Trả về None")
        except Exception as e:
            results[route_name] = {'success': False, 'error': str(e)}
            print(f"  ❌ Lỗi: {e}")
    
    return results

def run_test_suite(run_number):
    """Chạy toàn bộ test suite"""
    print("\n" + "=" * 80)
    print(f"LẦN TEST THỨ {run_number}")
    print("=" * 80)
    
    vm = get_vietmap_tools()
    geo_tools = GeoTools()
    
    if not vm.vietmap_api_key:
        print("❌ VIETMAP_API_KEY không được cấu hình!")
        return None
    
    print(f"✅ API Key: {vm.vietmap_api_key[:10]}...")
    
    # Test locations
    test_locations = [
        "Hà Nội",
        "Hồ Chí Minh",
        "Huế",
        "Đà Nẵng",
        "Cần Thơ",
        "Bắc Ninh",
        "Thành phố Huế",
        "tỉnh Thừa Thiên Huế"
    ]
    
    # Test routes (với tọa độ)
    test_routes_coords = [
        ("10.755222,106.662633", "10.7559910,106.6633234"),  # Test route ngắn
        ("21.028354,105.853798", "10.776486,106.701056"),    # Hà Nội -> HCM
    ]
    
    # Test routes (với địa chỉ)
    test_routes_addresses = [
        ("Hà Nội", "Hồ Chí Minh"),
        ("Đà Nẵng", "Huế"),
        ("Cần Thơ", "Bắc Ninh"),
    ]
    
    all_results = {
        'run_number': run_number,
        'geocoding': test_geocoding(vm, test_locations),
        'routing_coords': test_routing(vm, test_routes_coords),
        'geocoding_addresses': test_geocode_with_addresses(geo_tools, test_locations),
        'routing_addresses': test_routing_with_addresses(geo_tools, test_routes_addresses),
    }
    
    return all_results

def print_summary(all_runs):
    """In tổng kết kết quả"""
    print("\n" + "=" * 80)
    print("TỔNG KẾT KẾT QUẢ SAU 3 LẦN TEST")
    print("=" * 80)
    
    # Tính tỷ lệ thành công cho từng test
    test_categories = ['geocoding', 'routing_coords', 'geocoding_addresses', 'routing_addresses']
    
    for category in test_categories:
        print(f"\n📊 {category.upper()}:")
        print("-" * 80)
        
        # Lấy tất cả các keys từ tất cả các lần test
        all_keys = set()
        for run in all_runs:
            if run and category in run:
                all_keys.update(run[category].keys())
        
        for key in sorted(all_keys):
            success_count = 0
            total_count = 0
            errors = []
            
            for run in all_runs:
                if run and category in run and key in run[category]:
                    total_count += 1
                    if run[category][key].get('success'):
                        success_count += 1
                    else:
                        error = run[category][key].get('error', 'Unknown error')
                        if error not in errors:
                            errors.append(error)
            
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            status = "✅" if success_rate == 100 else "⚠️" if success_rate > 0 else "❌"
            
            print(f"  {status} {key}: {success_count}/{total_count} thành công ({success_rate:.1f}%)")
            if errors:
                print(f"     Lỗi: {', '.join(errors[:2])}")  # Chỉ hiển thị 2 lỗi đầu

def main():
    """Main function"""
    print("=" * 80)
    print("TEST CÁC API CỦA VIETMAP - 3 LẦN")
    print("=" * 80)
    
    all_runs = []
    
    for i in range(1, 4):
        try:
            results = run_test_suite(i)
            all_runs.append(results)
            
            # Nghỉ 1 giây giữa các lần test
            if i < 3:
                print("\n⏳ Đợi 1 giây trước lần test tiếp theo...")
                time.sleep(1)
        except Exception as e:
            print(f"\n❌ Lỗi trong lần test {i}: {e}")
            import traceback
            traceback.print_exc()
            all_runs.append(None)
    
    # In tổng kết
    print_summary(all_runs)
    
    print("\n" + "=" * 80)
    print("HOÀN TẤT TEST")
    print("=" * 80)

if __name__ == '__main__':
    main()

