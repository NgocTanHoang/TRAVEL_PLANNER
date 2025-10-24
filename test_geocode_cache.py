"""
Test Geocode Cache
Kiểm tra xem cache có hoạt động đúng không
"""

import sys
from pathlib import Path
import time

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from utils.geocoding_helper import get_geocoding_helper

def test_geocode_cache():
    """Test geocoding với cache"""
    
    print("="*80)
    print("🧪 TEST GEOCODE CACHE")
    print("="*80)
    
    helper = get_geocoding_helper()
    
    # Check cache stats
    stats = helper.get_cache_stats()
    print(f"\n📊 Current cache:")
    print(f"   Cached: {stats['total_cached']} addresses")
    print(f"   Cities: {stats['cities']}")
    
    # Test locations (famous Vietnam landmarks)
    test_locations = [
        {"name": "Dinh Độc Lập, TP.HCM", "lat": 10.7770, "lon": 106.6953},
        {"name": "Nhà thờ Đức Bà, TP.HCM", "lat": 10.7797, "lon": 106.6990},
        {"name": "Chợ Bến Thành", "lat": 10.7726, "lon": 106.6980},
        {"name": "Bảo tàng Chứng tích chiến tranh", "lat": 10.7795, "lon": 106.6918},
        {"name": "Landmark 81", "lat": 10.7944, "lon": 106.7218},
    ]
    
    print(f"\n🧪 Testing {len(test_locations)} locations...")
    print(f"{'='*80}\n")
    
    for i, loc in enumerate(test_locations, 1):
        print(f"{i}. {loc['name']}")
        print(f"   Coordinates: {loc['lat']}, {loc['lon']}")
        
        # First call (might be from cache or API)
        start = time.time()
        info = helper.get_detailed_info(loc['lat'], loc['lon'])
        duration_1 = time.time() - start
        
        if info:
            # Build address
            address_parts = []
            if info.get('street'):
                address_parts.append(info['street'])
            if info.get('suburb'):
                address_parts.append(info['suburb'])
            if info.get('city'):
                address_parts.append(info['city'])
            
            address = ', '.join(address_parts) if address_parts else info.get('formatted', 'N/A')[:80]
            print(f"   📍 Address: {address}")
            print(f"   ⏱️  Time: {duration_1:.3f}s")
        else:
            print(f"   ❌ No address found")
            print(f"   ⏱️  Time: {duration_1:.3f}s")
        
        # Second call (should be from cache - much faster)
        start = time.time()
        info_2 = helper.get_detailed_info(loc['lat'], loc['lon'])
        duration_2 = time.time() - start
        
        print(f"   ⏱️  Cached time: {duration_2:.3f}s")
        
        if duration_2 < 0.1:
            print(f"   ✅ CACHED! ({duration_2:.3f}s vs {duration_1:.3f}s - {duration_1/max(duration_2, 0.001):.0f}x faster)")
        else:
            print(f"   ⚠️  Not cached? (still took {duration_2:.3f}s)")
        
        print()
        
        # Small delay to respect API rate limit
        if i < len(test_locations):
            time.sleep(0.5)
    
    # Final stats
    stats_after = helper.get_cache_stats()
    print(f"\n{'='*80}")
    print(f"📊 Final cache stats:")
    print(f"   Cached: {stats_after['total_cached']} addresses")
    print(f"   New entries: {stats_after['total_cached'] - stats['total_cached']}")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_geocode_cache()

