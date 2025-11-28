"""
Test script tìm chuyến bay bằng FlightAPI
==========================================
Tìm chuyến bay từ Cần Thơ đến Hải Phòng:
- Ngày đi: 30/11/2025
- Ngày về: 3/12/2025
- 2 người lớn + 2 trẻ em
- Vé khứ hồi, hạng phổ thông
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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_price(price):
    """Format giá thành VND"""
    if price:
        return f"{price:,.0f}".replace(',', '.') + ' ₫'
    return 'N/A'

def test_flightapi_search():
    """Test tìm chuyến bay bằng FlightAPI"""
    print("="*80)
    print("TEST TÌM CHUYẾN BAY BẰNG FLIGHTAPI")
    print("="*80)
    print("Thông tin tìm kiếm:")
    print("  - Điểm đi: Cần Thơ (VCA)")
    print("  - Điểm đến: Hải Phòng (HPH)")
    print("  - Ngày đi: 30/11/2025")
    print("  - Ngày về: 3/12/2025")
    print("  - Hành khách: 2 người lớn + 2 trẻ em")
    print("  - Hạng vé: Phổ thông (Economy)")
    print("  - Loại: Khứ hồi")
    print("="*80)
    
    # Thông tin tìm kiếm
    origin = "Cần Thơ"
    destination = "Hải Phòng"
    departure_date = "2025-11-30"
    return_date = "2025-12-03"
    adults = 2
    children = 2
    total_passengers = adults + children
    
    # Test FlightAPI
    print("\n[TEST] FLIGHTAPI")
    print("-" * 80)
    try:
        flight_tools = get_flight_tools()
        
        # Kiểm tra API key
        if not flight_tools.flightapi_key:
            print("❌ FLIGHTAPI_KEY chưa được cấu hình trong .env")
            return
        
        print(f"✅ FLIGHTAPI_KEY đã được cấu hình")
        print(f"   API Key: {flight_tools.flightapi_key[:10]}...")
        
        # Gọi API trực tiếp
        print(f"\n🔍 Đang tìm kiếm chuyến bay...")
        print(f"   Từ: {origin} (VCA)")
        print(f"   Đến: {destination} (HPH)")
        print(f"   Ngày đi: {departure_date}")
        print(f"   Ngày về: {return_date}")
        print(f"   {adults} người lớn + {children} trẻ em")
        
        # Lưu ý: FlightAPI hiện tại chỉ hỗ trợ adults trong URL path
        # Để hỗ trợ children, cần cập nhật code để thêm vào URL
        result = flight_tools._search_via_flightapi(
            origin_iata="VCA",
            dest_iata="HPH",
            departure_date=departure_date,
            return_date=return_date,
            passengers=adults,
            children=children,
            infants=0
        )
        
        if result and result.get('price_vnd') and result.get('price_vnd') > 0:
            print(f"\n✅ Tìm thấy chuyến bay!")
            print(f"   Giá: {format_price(result.get('price_vnd'))}")
            print(f"   Loại: {result.get('route_type', 'N/A')}")
            print(f"   Số hành khách: {result.get('passengers', 'N/A')}")
            print(f"   Nguồn: {result.get('source', 'N/A')}")
            print(f"   Currency: {result.get('currency', 'N/A')}")
            
            if result.get('raw_data'):
                print(f"\n   📋 Thông tin chi tiết từ API:")
                raw = result.get('raw_data', {})
                if isinstance(raw, dict):
                    # Hiển thị một số thông tin quan trọng
                    if raw.get('itineraries'):
                        print(f"      Số chuyến bay tìm thấy: {len(raw.get('itineraries', []))}")
                    if raw.get('flights'):
                        print(f"      Số chuyến bay tìm thấy: {len(raw.get('flights', []))}")
                    if raw.get('currency'):
                        print(f"      Currency: {raw.get('currency')}")
                    if raw.get('query'):
                        query = raw.get('query', {})
                        print(f"      Query: {query.get('currency', 'N/A')} - {query.get('adults', 'N/A')} adults")
        else:
            print(f"\n❌ Không tìm thấy chuyến bay hoặc có lỗi")
            if result:
                print(f"   Result keys: {list(result.keys())}")
                if result.get('error'):
                    print(f"   Lỗi: {result.get('error')}")
                if result.get('raw_data'):
                    raw = result.get('raw_data', {})
                    print(f"   Raw data keys: {list(raw.keys())[:10] if isinstance(raw, dict) else 'Not a dict'}")
                    # In một phần raw data để debug
                    import json
                    print(f"   Raw data sample: {json.dumps(raw, indent=2, default=str)[:500]}")
            else:
                print(f"   Result is None or empty")
                
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ Hoàn tất test!")
    print("="*80)

if __name__ == "__main__":
    test_flightapi_search()

