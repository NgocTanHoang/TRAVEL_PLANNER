"""
Script chạy thu thập dữ liệu TOÀN BỘ cho các tỉnh thành Việt Nam
Sử dụng Geoapify API - 3000 requests/day FREE
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.collect_city_data import CityDataCollector
from config.vietnam_cities import CITIES_NEED_DATA, VIETNAM_CITIES

def main():
    """Chạy thu thập dữ liệu toàn bộ"""
    
    print("="*80)
    print("🚀 THU THẬP DỮ LIỆU TOÀN BỘ CÁC TỈNH THÀNH VIỆT NAM")
    print("="*80)
    print()
    print(f"📊 Tổng số tỉnh cần thu thập: {len(CITIES_NEED_DATA)}")
    print(f"🔑 API: Geoapify (3000 requests/day)")
    print(f"⏱️  Thời gian ước tính: ~{len(CITIES_NEED_DATA) * 15 / 60:.0f} phút")
    print()
    
    # Hỏi user xác nhận
    choice = input("Bạn có muốn tiếp tục? (y/n): ").strip().lower()
    if choice != 'y':
        print("❌ Đã hủy")
        return
    
    # Tạo collector
    collector = CityDataCollector()
    
    # Chạy thu thập
    print("\n" + "="*80)
    print("🎬 BẮT ĐẦU THU THẬP...")
    print("="*80)
    
    results = collector.run_collection(
        cities_to_collect=CITIES_NEED_DATA,
        limit=None  # Thu thập toàn bộ
    )
    
    # Print summary
    print("\n" + "="*80)
    print("✅ HOÀN THÀNH THU THẬP DỮ LIỆU!")
    print("="*80)
    
    successful = sum(1 for r in results.values() if 'error' not in r)
    failed = sum(1 for r in results.values() if 'error' in r)
    
    print(f"\n📊 Tổng kết:")
    print(f"   ✅ Thành công: {successful}/{len(CITIES_NEED_DATA)} tỉnh")
    print(f"   ❌ Thất bại: {failed}/{len(CITIES_NEED_DATA)} tỉnh")
    
    total_hotels = sum(r.get('hotels', 0) for r in results.values())
    total_restaurants = sum(r.get('restaurants', 0) for r in results.values())
    total_attractions = sum(r.get('attractions', 0) for r in results.values())
    
    print(f"\n📍 Dữ liệu thu thập:")
    print(f"   🏨 Hotels: {total_hotels}")
    print(f"   🍜 Restaurants: {total_restaurants}")
    print(f"   🏛️ Attractions: {total_attractions}")
    print(f"   📊 Tổng: {total_hotels + total_restaurants + total_attractions} địa điểm")
    
    if failed > 0:
        print(f"\n⚠️  Các tỉnh thất bại:")
        for city, result in results.items():
            if 'error' in result:
                print(f"   - {VIETNAM_CITIES[city]['name_vi']} ({city}): {result['error'][:50]}")
    
    print("\n" + "="*80)
    print("🎉 Dữ liệu đã được lưu vào:")
    print("   - data/hotels_large.csv")
    print("   - data/restaurants_large.csv")
    print("   - data/attractions_large.csv")
    print("="*80)
    
    print("\n💡 Bước tiếp theo:")
    print("   1. Chạy: python scripts/populate_vector_db.py")
    print("   2. Chạy: python run_ui.py")
    print()

if __name__ == "__main__":
    main()

