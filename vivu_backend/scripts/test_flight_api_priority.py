"""
Test script kiểm tra thứ tự ưu tiên API tìm kiếm chuyến bay
=============================================================
Kiểm tra xem FlightAPI có được ưu tiên trước SerpAPI không
"""
import os
import sys
import codecs
import django
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

import logging
from tools.flight_tools import get_flight_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_priority():
    """Test thứ tự ưu tiên API"""
    print("="*80)
    print("TEST THỨ TỰ ƯU TIÊN API TÌM KIẾM CHUYẾN BAY")
    print("="*80)
    
    flight_tools = get_flight_tools()
    
    print("\n📋 Cấu hình API hiện tại:")
    print(f"   ✅ FlightAPI: {'Có' if flight_tools.flightapi_key else 'Không'}")
    print(f"   ✅ SerpAPI: {'Có' if (flight_tools.serpapi and flight_tools.serpapi.api_key) else 'Không'}")
    print(f"   ✅ Amadeus: {'Có' if (flight_tools.amadeus and flight_tools.amadeus.is_available()) else 'Không'}")
    
    print("\n🔍 Thứ tự ưu tiên mong đợi:")
    print("   1. Amadeus API (nếu có)")
    print("   2. FlightAPI (ưu tiên chính)")
    print("   3. SerpAPI (fallback)")
    print("   4. Travelpayouts API (nếu có)")
    
    print("\n🧪 Test tìm kiếm chuyến bay...")
    print("   Từ: Cần Thơ (VCA)")
    print("   Đến: Hải Phòng (HPH)")
    print("   Ngày đi: 2025-11-30")
    print("   Ngày về: 2025-12-03")
    print("   2 người lớn")
    
    result = flight_tools.search_flight_prices(
        origin="Cần Thơ",
        destination="Hải Phòng",
        departure_date="2025-11-30",
        return_date="2025-12-03",
        passengers=2
    )
    
    if result and result.get('price_vnd') and result.get('price_vnd') > 0:
        print(f"\n✅ Tìm thấy chuyến bay!")
        print(f"   Giá: {result.get('price_vnd'):,.0f} ₫".replace(',', '.'))
        print(f"   Nguồn: {result.get('source', 'N/A')}")
        print(f"   Loại: {result.get('route_type', 'N/A')}")
        
        source = result.get('source', '')
        if source == 'flightapi':
            print(f"\n   ✅ Đúng! Đã sử dụng FlightAPI (ưu tiên)")
        elif source == 'serpapi':
            print(f"\n   ⚠️  Đã sử dụng SerpAPI (fallback)")
            if not flight_tools.flightapi_key:
                print(f"      Lý do: FlightAPI không được cấu hình")
        elif source == 'amadeus':
            print(f"\n   ℹ️  Đã sử dụng Amadeus API (ưu tiên cao nhất)")
        else:
            print(f"\n   ℹ️  Đã sử dụng {source}")
    else:
        print(f"\n❌ Không tìm thấy chuyến bay")
        if result.get('error'):
            print(f"   Lỗi: {result.get('error')}")
    
    print("\n" + "="*80)
    print("✅ Hoàn tất test!")
    print("="*80)

if __name__ == "__main__":
    test_api_priority()

