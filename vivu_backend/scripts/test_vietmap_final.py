# -*- coding: utf-8 -*-
"""Test các API VietMap - 3 lần"""
import os, sys, django
from pathlib import Path
import codecs

# Fix encoding cho Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from tools.vietmap_tools import get_vietmap_tools
from tools.geo_tools import GeoTools

def test_run(run_num):
    print(f"\n{'='*60}")
    print(f"LAN TEST {run_num}")
    print(f"{'='*60}")
    
    vm = get_vietmap_tools()
    geo = GeoTools()
    
    results = {'geocode': {}, 'route_coords': {}, 'route_addresses': {}}
    
    # Test 1: Geocode
    print("\n1. GEOCODE:")
    test_locations = ["Hà Nội", "Huế", "Hồ Chí Minh", "Đà Nẵng", "Cần Thơ"]
    for loc in test_locations:
        try:
            r = vm.geocode(loc)
            if r:
                results['geocode'][loc] = {'success': True, 'lat': r.get('lat'), 'lon': r.get('lon')}
                print(f"  {loc}: OK - {r.get('lat'):.4f}, {r.get('lon'):.4f}")
            else:
                results['geocode'][loc] = {'success': False}
                print(f"  {loc}: FAIL - None")
        except Exception as e:
            results['geocode'][loc] = {'success': False, 'error': str(e)}
            print(f"  {loc}: FAIL - {e}")
    
    # Test 2: Route với tọa độ
    print("\n2. ROUTE (coords):")
    try:
        r = vm.calculate_distance_time("21.028354,105.853798", "10.776486,106.701056", "car")
        if r:
            results['route_coords']['HN->HCM'] = {'success': True, 'distance': r.get('distance_km'), 'duration': r.get('duration_minutes')}
            print(f"  HN->HCM: OK - {r.get('distance_km'):.1f}km, {r.get('duration_minutes'):.1f}min")
        else:
            results['route_coords']['HN->HCM'] = {'success': False}
            print(f"  HN->HCM: FAIL - None")
    except Exception as e:
        results['route_coords']['HN->HCM'] = {'success': False, 'error': str(e)}
        print(f"  HN->HCM: FAIL - {e}")
    
    # Test 3: Route với địa chỉ
    print("\n3. ROUTE (addresses):")
    test_routes = [("Đà Nẵng", "Huế"), ("Cần Thơ", "Bắc Ninh")]
    for origin, dest in test_routes:
        route_name = f"{origin}->{dest}"
        try:
            r = geo.calculate_distance_time(origin, dest, profile='driving-car', use_vietmap=True)
            if r:
                results['route_addresses'][route_name] = {'success': True, 'distance': r.get('distance_km'), 'duration': r.get('duration_minutes')}
                print(f"  {route_name}: OK - {r.get('distance_km'):.1f}km, {r.get('duration_minutes'):.1f}min")
            else:
                results['route_addresses'][route_name] = {'success': False}
                print(f"  {route_name}: FAIL - None")
        except Exception as e:
            results['route_addresses'][route_name] = {'success': False, 'error': str(e)}
            print(f"  {route_name}: FAIL - {e}")
    
    return results

def main():
    print("="*60)
    print("TEST CAC API CUA VIETMAP - 3 LAN")
    print("="*60)
    
    all_results = []
    
    for i in range(1, 4):
        try:
            results = test_run(i)
            all_results.append(results)
            if i < 3:
                import time
                time.sleep(1)
        except Exception as e:
            print(f"\nLOI TRONG LAN TEST {i}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append(None)
    
    # Tổng kết
    print(f"\n{'='*60}")
    print("TONG KET")
    print(f"{'='*60}")
    
    # Tính tỷ lệ thành công
    categories = ['geocode', 'route_coords', 'route_addresses']
    for cat in categories:
        print(f"\n{cat.upper()}:")
        all_keys = set()
        for r in all_results:
            if r and cat in r:
                all_keys.update(r[cat].keys())
        
        for key in sorted(all_keys):
            success = sum(1 for r in all_results if r and cat in r and key in r[cat] and r[cat][key].get('success'))
            total = sum(1 for r in all_results if r and cat in r and key in r[cat])
            rate = (success / total * 100) if total > 0 else 0
            status = "OK" if rate == 100 else "FAIL"
            print(f"  {key}: {success}/{total} ({rate:.0f}%) - {status}")
    
    print(f"\n{'='*60}")
    print("HOAN TAT")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

