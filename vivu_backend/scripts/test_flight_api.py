"""
Test script tìm chuyến bay bằng API
====================================
Tìm chuyến bay từ TP.HCM đến Huế:
- Ngày đi: 29/11/2025
- Ngày về: 2/12/2025
- 2 người lớn + 1 trẻ em
- Vé phổ thông
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

import logging
import pandas as pd
from tools.flight_tools import get_flight_tools
from tools.serpapi_tools import get_serpapi_tools
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_price(price):
    """Format giá thành VND"""
    if price:
        return f"{price:,.0f}".replace(',', '.') + ' ₫'
    return 'N/A'

def test_flight_search():
    """Test tìm chuyến bay"""
    print("="*80)
    print("TEST TÌM CHUYẾN BAY BẰNG API")
    print("="*80)
    print("Thông tin tìm kiếm:")
    print("  - Điểm đi: TP.HCM (SGN)")
    print("  - Điểm đến: Huế (HUI)")
    print("  - Ngày đi: 29/11/2025")
    print("  - Ngày về: 2/12/2025")
    print("  - Hành khách: 2 người lớn + 1 trẻ em")
    print("  - Hạng vé: Phổ thông (Economy)")
    print("="*80)
    
    # Thông tin tìm kiếm
    origin = "TP. Hồ Chí Minh"
    destination = "Huế"
    departure_date = "2025-11-29"
    return_date = "2025-12-02"
    adults = 2
    children = 1
    total_passengers = adults + children
    
    # Test 1: FlightTools (tổng hợp nhiều API)
    print("\n[1] TEST FLIGHTTOOLS (Tổng hợp nhiều API)")
    print("-" * 80)
    try:
        flight_tools = get_flight_tools()
        
        # FlightTools hiện tại chỉ hỗ trợ passengers (tổng số), chưa phân biệt adults/children
        result = flight_tools.search_flight_prices(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            passengers=total_passengers
        )
        
        print(f"✅ Kết quả từ {result.get('source', 'unknown')}:")
        print(f"   Giá: {format_price(result.get('price_vnd'))}")
        print(f"   Loại: {result.get('route_type', 'N/A')}")
        print(f"   Số hành khách: {result.get('passengers', 'N/A')}")
        print(f"   Hãng bay: {result.get('airline', 'N/A')}")
        print(f"   Số hiệu chuyến bay: {result.get('flight_number', 'N/A')}")
        
        if result.get('all_flights'):
            print(f"\n   📋 Tất cả chuyến bay ({len(result.get('all_flights', []))} chuyến):")
            for idx, flight in enumerate(result.get('all_flights', [])[:5], 1):
                print(f"      [{idx}] {flight.get('airline', 'N/A')} - {format_price(flight.get('price_vnd', flight.get('price', 0)))}")
        
        if result.get('error'):
            print(f"   ⚠️  Lỗi: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: SerpAPI trực tiếp (nếu có)
    print("\n[2] TEST SERPAPI TRỰC TIẾP")
    print("-" * 80)
    try:
        serpapi = get_serpapi_tools()
        
        if not serpapi.api_key:
            print("⚠️  SerpAPI không được cấu hình (SERPAPI_API_KEY không có)")
        else:
            result = serpapi.search_flights(
                origin="SGN",
                destination="HUI",
                departure_date=departure_date,
                return_date=return_date,
                currency="VND",
                language="vi",
                country="vn"
            )
            
            if result.get('status') == 'success':
                flights = result.get('flights', [])
                print(f"✅ Tìm thấy {len(flights)} chuyến bay:")
                
                # Tính giá cho 2 người lớn + 1 trẻ em
                # Trẻ em thường được tính 75% giá người lớn
                adult_price_multiplier = 2
                child_price_multiplier = 0.75
                total_multiplier = adult_price_multiplier + child_price_multiplier
                
                # Sắp xếp theo giá và lấy top 5
                sorted_flights = sorted(flights, key=lambda x: x.get('price', float('inf')))[:5]
                
                print(f"\n📋 TOP {len(sorted_flights)} CHUYẾN RẺ NHẤT (Giá cho {adults} người lớn + {children} trẻ em):")
                print("-" * 80)
                
                # List để lưu kết quả
                flight_results = []
                
                for idx, flight in enumerate(sorted_flights, 1):
                    base_price = flight.get('price', 0)
                    # Giá cho 1 người lớn, nhân với số người
                    total_price = base_price * total_multiplier
                    
                    # Parse thời gian bay (duration có thể là số phút)
                    duration = flight.get('duration', 0)
                    if isinstance(duration, (int, float)):
                        hours = int(duration // 60)
                        minutes = int(duration % 60)
                        duration_str = f"{hours} giờ {minutes} phút" if hours > 0 else f"{minutes} phút"
                    else:
                        duration_str = str(duration)
                    
                    # Parse giờ khởi hành và đến
                    dep_time = flight.get('departure_time', '')
                    arr_time = flight.get('arrival_time', '')
                    
                    # Nếu là datetime string, chỉ lấy phần time
                    if isinstance(dep_time, str) and 'T' in dep_time:
                        dep_time = dep_time.split('T')[1].split('+')[0][:5]
                    if isinstance(arr_time, str) and 'T' in arr_time:
                        arr_time = arr_time.split('T')[1].split('+')[0][:5]
                    
                    airline = flight.get('airline', 'Unknown')
                    flight_number = flight.get('flight_number', '')
                    
                    # Nếu airline vẫn Unknown, nhận diện từ flight number
                    if airline == 'Unknown' and flight_number:
                        airline_codes = {
                            'VJ': 'VietJet',
                            'VN': 'Vietnam Airlines',
                            'QH': 'Bamboo Airways',
                            'BL': 'Pacific Airlines',
                            'JQ': 'Jetstar Pacific'
                        }
                        code = flight_number.replace(' ', '')[:2].upper()
                        if code in airline_codes:
                            airline = airline_codes[code]
                    
                    print(f"\n[{idx}] {airline}")
                    if flight_number:
                        print(f"    Số hiệu chuyến bay: {flight_number}")
                    print(f"    Giá (1 người lớn): {format_price(base_price)}")
                    print(f"    Giá tổng ({adults} người lớn + {children} trẻ em): {format_price(total_price)}")
                    print(f"    Giờ khởi hành: {dep_time or 'N/A'}")
                    print(f"    Giờ đến: {arr_time or 'N/A'}")
                    print(f"    Thời gian bay: {duration_str}")
                    print(f"    Loại: {flight.get('type', 'N/A')}")
                    
                    # Lấy thông tin sân bay từ flight data
                    dep_airport = flight.get('departure_airport', {})
                    arr_airport = flight.get('arrival_airport', {})
                    
                    if dep_airport:
                        dep_airport_name = dep_airport.get('name', '')
                        dep_airport_id = dep_airport.get('id', '')
                        if dep_airport_name or dep_airport_id:
                            print(f"    Từ: {dep_airport_name} ({dep_airport_id})")
                    
                    if arr_airport:
                        arr_airport_name = arr_airport.get('name', '')
                        arr_airport_id = arr_airport.get('id', '')
                        if arr_airport_name or arr_airport_id:
                            print(f"    Đến: {arr_airport_name} ({arr_airport_id})")
                    
                    # Lưu kết quả vào list để export CSV
                    flight_results.append({
                        'airline': airline,
                        'flight_number': flight_number,
                        'price_per_adult': base_price,
                        'total_price': total_price,
                        'departure_time': dep_time,
                        'arrival_time': arr_time,
                        'duration': duration_str,
                        'departure_airport': dep_airport.get('name', '') + f" ({dep_airport.get('id', '')})" if dep_airport.get('name') or dep_airport.get('id') else 'N/A',
                        'arrival_airport': arr_airport.get('name', '') + f" ({arr_airport.get('id', '')})" if arr_airport.get('name') or arr_airport.get('id') else 'N/A',
                        'type': flight.get('type', 'N/A')
                    })
                
                if result.get('lowest_price'):
                    lowest_base = result.get('lowest_price', 0)
                    lowest_total = lowest_base * total_multiplier
                    print(f"\n   💰 Giá thấp nhất (1 người lớn): {format_price(lowest_base)}")
                    print(f"   💰 Giá thấp nhất ({adults} người lớn + {children} trẻ em): {format_price(lowest_total)}")
                
                if result.get('typical_price_range'):
                    price_range = result.get('typical_price_range', [])
                    if len(price_range) >= 2:
                        range_min = price_range[0] * total_multiplier
                        range_max = price_range[1] * total_multiplier
                        print(f"   📊 Khoảng giá điển hình ({adults} người lớn + {children} trẻ em): {format_price(range_min)} - {format_price(range_max)}")
                
                # Lưu kết quả vào CSV sau khi xử lý tất cả flights
                if flight_results:
                    df = pd.DataFrame(flight_results)
                    filename = "flight_search_results.csv"
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"\n💾 Đã lưu {len(flight_results)} chuyến bay vào: {filename}")
            else:
                print(f"❌ Lỗi: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Amadeus API (nếu có)
    print("\n[3] TEST AMADEUS API")
    print("-" * 80)
    try:
        from tools.amadeus_tools import get_amadeus_tools
        amadeus = get_amadeus_tools()
        
        if not amadeus or not amadeus.is_available():
            print("⚠️  Amadeus API không được cấu hình hoặc không khả dụng")
        else:
            result = amadeus.search_flights(
                origin_iata="SGN",
                destination_iata="HUI",
                departure_date=departure_date,
                return_date=return_date,
                passengers=total_passengers
            )
            
            if result.get('status') == 'success':
                flights = result.get('flights', [])
                print(f"✅ Tìm thấy {len(flights)} chuyến bay:")
                
                # Sắp xếp theo giá
                sorted_flights = sorted(flights, key=lambda x: x.get('price_vnd', float('inf')))[:5]
                
                for idx, flight in enumerate(sorted_flights, 1):
                    print(f"\n   [{idx}] {format_price(flight.get('price_vnd', 0))}")
                    print(f"       Hãng bay: {flight.get('segments', [{}])[0].get('carrierCode', 'N/A') if flight.get('segments') else 'N/A'}")
                    print(f"       Số hiệu: {flight.get('segments', [{}])[0].get('number', 'N/A') if flight.get('segments') else 'N/A'}")
                    print(f"       Thời gian bay: {flight.get('duration', 'N/A')}")
            else:
                print(f"❌ Lỗi: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"⚠️  Amadeus API không khả dụng: {e}")
    
    print("\n" + "="*80)
    print("✅ Hoàn tất test!")
    print("="*80)

if __name__ == "__main__":
    test_flight_search()

