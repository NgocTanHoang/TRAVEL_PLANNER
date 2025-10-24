"""
Thu thập dữ liệu cho 10 tỉnh ưu tiên cao (priority 2)
Test nhanh trước khi chạy full
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.collect_city_data import CityDataCollector
from config.vietnam_cities import get_cities_by_priority

def main():
    """Thu thập 10 tỉnh ưu tiên cao"""
    
    # Lấy tỉnh priority 2 (quan trọng)
    priority_cities = list(get_cities_by_priority(2).keys())
    
    print("="*80)
    print("🚀 THU THẬP 10 TỈNH ƯU TIÊN CAO")
    print("="*80)
    print()
    print(f"📍 Danh sách ({len(priority_cities[:10])} tỉnh):")
    
    from config.vietnam_cities import VIETNAM_CITIES
    for i, city in enumerate(priority_cities[:10], 1):
        print(f"   {i}. {VIETNAM_CITIES[city]['name_vi']}")
    
    print()
    print(f"⏱️  Thời gian ước tính: ~2-3 phút")
    print()
    
    choice = input("Bắt đầu thu thập? (y/n): ").strip().lower()
    if choice != 'y':
        print("❌ Đã hủy")
        return
    
    collector = CityDataCollector()
    results = collector.run_collection(
        cities_to_collect=priority_cities[:10],
        limit=10
    )
    
    print("\n✅ HOÀN THÀNH!")
    print(f"   Thu thập thành công: {len([r for r in results.values() if 'error' not in r])}/10 tỉnh")
    
    total = sum(r.get('hotels', 0) + r.get('restaurants', 0) + r.get('attractions', 0) for r in results.values())
    print(f"   Tổng địa điểm: {total}")

if __name__ == "__main__":
    main()

