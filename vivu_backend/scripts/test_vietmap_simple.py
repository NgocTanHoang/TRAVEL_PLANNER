# -*- coding: utf-8 -*-
"""Test đơn giản các API VietMap"""
import os, sys, django
from pathlib import Path

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
    
    # Test 1: Geocode
    print("\n1. GEOCODE:")
    for loc in ["Hà Nội", "Huế", "Hồ Chí Minh"]:
        r = vm.geocode(loc)
        if r:
            print(f"  {loc}: OK - {r.get('lat'):.4f}, {r.get('lon'):.4f}")
        else:
            print(f"  {loc}: FAIL")
    
    # Test 2: Route với tọa độ
    print("\n2. ROUTE (coords):")
    r = vm.calculate_distance_time("21.028354,105.853798", "10.776486,106.701056", "car")
    if r:
        print(f"  HN->HCM: OK - {r.get('distance_km'):.1f}km, {r.get('duration_minutes'):.1f}min")
    else:
        print(f"  HN->HCM: FAIL")
    
    # Test 3: Route với địa chỉ
    print("\n3. ROUTE (addresses):")
    r = geo.calculate_distance_time("Đà Nẵng", "Huế", profile='driving-car', use_vietmap=True)
    if r:
        print(f"  DN->Huế: OK - {r.get('distance_km'):.1f}km, {r.get('duration_minutes'):.1f}min")
    else:
        print(f"  DN->Huế: FAIL")

if __name__ == '__main__':
    for i in range(1, 4):
        test_run(i)
        if i < 3:
            import time
            time.sleep(1)
    print(f"\n{'='*60}")
    print("HOAN TAT")
    print(f"{'='*60}")
