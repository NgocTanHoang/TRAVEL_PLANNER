"""
Test Script - Tính chi phí du lịch toàn bộ
===========================================
Test tính toán chi phí từ Gò Vấp, TPHCM đến Vũng Tàu
Phong cách: Lãng mạn (Romantic)
"""
import os
import sys
import django
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    # Set UTF-8 encoding for console output
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    
    # Set console code page to UTF-8
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

# Setup Django
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

import asyncio
from vivu_backend.tools.geo_tools import get_geo_tools
from vivu_backend.tools.transport_tools import get_transport_tools
from vivu_backend.tools.flight_tools import get_flight_tools
from vivu_backend.tools.accommodation_tools import get_accommodation_tools
from vivu_backend.tools.activities_tools import get_activities_tools
from vivu_backend.tools.budget_tools import get_budget_tools
from vivu_backend.agents.travel_agents.transport_agent import TransportAgent
from vivu_backend.agents.travel_agents.accommodation_agent import AccommodationAgent
from vivu_backend.agents.travel_agents.activities_agent import ActivitiesAgent
from vivu_backend.agents.travel_agents.budget_agent import BudgetAgent
from vivu_backend.agents.travel_agents.orchestrator_agent import OrchestratorAgent
from datetime import datetime, timedelta

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_subsection(title):
    print(f"\n--- {title} ---")

async def test_travel_cost():
    """Test tính chi phí du lịch toàn bộ"""
    
    # Thông tin chuyến đi
    origin = "Gò Vấp, TPHCM"
    destination = "Vũng Tàu"
    travel_style = "romantic"
    days = 3
    travelers = 2
    rooms = 1
    start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    print_section("TEST TÍNH CHI PHÍ DU LỊCH")
    print(f"📍 Điểm xuất phát: {origin}")
    print(f"📍 Điểm đến: {destination}")
    print(f"💑 Phong cách: {travel_style} (Lãng mạn)")
    print(f"📅 Số ngày: {days}")
    print(f"👥 Số người: {travelers}")
    print(f"🛏️  Số phòng: {rooms}")
    print(f"📆 Ngày bắt đầu: {start_date}")
    
    # Initialize tools
    geo_tools = get_geo_tools()
    transport_tools = get_transport_tools()
    flight_tools = get_flight_tools()
    accommodation_tools = get_accommodation_tools()
    activities_tools = get_activities_tools()
    budget_tools = get_budget_tools()
    
    # ==========================================
    # 1. GEOCODING & ROUTING
    # ==========================================
    print_section("1. GEOCODING & TÍNH KHOẢNG CÁCH")
    
    origin_coords = geo_tools.geocode(origin, use_vietmap=True)
    dest_coords = geo_tools.geocode(destination, use_vietmap=True)
    
    if origin_coords:
        print(f"✅ Origin: {origin_coords.get('formatted_address', origin)}")
        print(f"   Tọa độ: ({origin_coords['lat']}, {origin_coords['lon']})")
    else:
        print(f"❌ Không thể geocode: {origin}")
        return
    
    if dest_coords:
        print(f"✅ Destination: {dest_coords.get('formatted_address', destination)}")
        print(f"   Tọa độ: ({dest_coords['lat']}, {dest_coords['lon']})")
    else:
        print(f"❌ Không thể geocode: {destination}")
        return
    
    # Tính khoảng cách
    route_info = geo_tools.calculate_distance_time(
        origin, destination, profile='driving-car', use_vietmap=True
    )
    
    if route_info:
        print(f"\n📏 Khoảng cách: {route_info['distance_km']} km")
        print(f"⏱️  Thời gian: {route_info['duration_minutes']} phút (~{route_info['duration_minutes']/60:.1f} giờ)")
        distance_km = route_info['distance_km']
    else:
        print("⚠️  Không thể tính route, sử dụng khoảng cách ước tính")
        # Tính khoảng cách đường thẳng (Haversine)
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(origin_coords['lat']), radians(origin_coords['lon'])
        lat2, lon2 = radians(dest_coords['lat']), radians(dest_coords['lon'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_km = 6371 * c
        print(f"📏 Khoảng cách ước tính (đường thẳng): {distance_km:.1f} km")
    
    # ==========================================
    # 2. TRANSPORT COST
    # ==========================================
    print_section("2. CHI PHÍ DI CHUYỂN")
    
    # So sánh tất cả phương tiện
    transport_comparison = transport_tools.compare_all_transport_options(
        origin, destination, travelers=travelers, distance_km=distance_km
    )
    
    print(f"\n📊 So sánh các phương tiện:")
    for i, option in enumerate(transport_comparison.get('options', [])[:5], 1):
        print(f"\n{i}. {option.get('method_name', option['method'])}")
        print(f"   💰 Chi phí: {option['cost_vnd']:,} VNĐ")
        print(f"   💰/người: {option['cost_per_person']:,} VNĐ")
        print(f"   ⏱️  Thời gian: {option['duration_minutes']:.1f} phút (~{option['duration_minutes']/60:.1f} giờ)")
        print(f"   📝 {option.get('description', '')}")
    
    cheapest = transport_comparison.get('cheapest')
    fastest = transport_comparison.get('fastest')
    
    if cheapest:
        print(f"\n💰 Rẻ nhất: {cheapest.get('method_name')} - {cheapest['cost_vnd']:,} VNĐ")
    if fastest:
        print(f"⚡ Nhanh nhất: {fastest.get('method_name')} - {fastest['duration_minutes']:.1f} phút")
    
    # Đề xuất phương tiện
    suggestion = transport_tools.suggest_transport(
        origin, destination, distance_km=distance_km, travelers=travelers
    )
    transport_cost = suggestion.get('estimated_cost_vnd', 0)
    print(f"\n✅ Đề xuất: {suggestion.get('method_name')} - {transport_cost:,} VNĐ")
    
    # ==========================================
    # 3. ACCOMMODATION COST
    # ==========================================
    print_section("3. CHI PHÍ LƯU TRÚ")
    
    check_in = start_date
    check_out = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Tìm khách sạn
    hotels = accommodation_tools.search_hotels(
        city=destination,
        check_in=check_in,
        check_out=check_out,
        guests=travelers,
        rooms=rooms
    )
    
    print(f"\n🏨 Tìm thấy {len(hotels)} khách sạn")
    
    if hotels:
        print(f"\n📋 Top 5 khách sạn:")
        for i, hotel in enumerate(hotels[:5], 1):
            print(f"\n{i}. {hotel.get('name', 'Unknown')}")
            print(f"   💰 Giá/đêm: {hotel.get('price_per_night', 0):,} VNĐ")
            print(f"   ⭐ {hotel.get('stars', 'N/A')} sao")
            print(f"   ⭐ Rating: {hotel.get('rating', 0)}/5")
            print(f"   📍 {hotel.get('address', 'N/A')}")
    
    # Tính chi phí lưu trú
    accommodation_agent = AccommodationAgent()
    state = {
        'destination': destination,
        'check_in': check_in,
        'check_out': check_out,
        'guests': travelers,
        'rooms': rooms,
        'travel_style': travel_style,
        'days': days
    }
    
    state = await accommodation_agent.execute(state)
    accommodation_cost = state.get('accommodation_cost', 0)
    
    print(f"\n✅ Chi phí lưu trú ước tính: {accommodation_cost:,} VNĐ")
    print(f"   ({accommodation_cost/days/rooms:,} VNĐ/phòng/đêm)")
    
    # ==========================================
    # 4. ACTIVITIES & DINING COST
    # ==========================================
    print_section("4. CHI PHÍ HOẠT ĐỘNG & ĂN UỐNG")
    
    # Sử dụng ActivitiesAgent để có đầy đủ fallback logic
    print("   Đang tìm kiếm hoạt động và nhà hàng...")
    
    activities_agent = ActivitiesAgent()
    state = {
        'destination': destination,
        'travel_style': travel_style,
        'travelers': travelers,
        'days': days
    }
    
    try:
        state = await activities_agent.execute(state)
        activities = state.get('activities', [])
        activities_cost = state.get('activities_cost', 0)
    except Exception as e:
        print(f"⚠️  Lỗi khi tìm activities với ActivitiesAgent: {e}")
        print("   Sử dụng tools trực tiếp...")
        
        # Fallback: Sử dụng tools trực tiếp
        try:
            activities = activities_tools.search_activities(
                destination=destination,
                travel_style=travel_style
            )
        except Exception as e2:
            print(f"⚠️  Lỗi khi tìm activities với tools: {e2}")
            activities = []
        
        # Nếu vẫn không có activities, tạo generic fallback
        if not activities or len(activities) == 0:
            print("   Tạo generic fallback activities...")
            activities = [
                {
                    'name': f'Tham quan {destination}',
                    'type': 'sightseeing',
                    'price_per_person': 0,
                    'duration_hours': 2.0,
                    'description': f'Khám phá các điểm tham quan nổi tiếng tại {destination}',
                    'address': destination,
                    'source': 'generic_fallback'
                },
                {
                    'name': f'Bảo tàng/Văn hóa {destination}',
                    'type': 'museum',
                    'price_per_person': 50000,
                    'duration_hours': 1.5,
                    'description': f'Tìm hiểu văn hóa và lịch sử địa phương tại {destination}',
                    'address': destination,
                    'source': 'generic_fallback'
                },
                {
                    'name': f'Địa điểm du lịch {destination}',
                    'type': 'sightseeing',
                    'price_per_person': 30000,
                    'duration_hours': 2.0,
                    'description': f'Tham quan các địa điểm du lịch nổi tiếng tại {destination}',
                    'address': destination,
                    'source': 'generic_fallback'
                }
            ]
        
        # Tính chi phí hoạt động
        activities_cost = activities_tools.calculate_activity_cost(
            activities=activities,
            travelers=travelers
        )
    
    restaurants = activities_tools.search_restaurants(destination=destination)
    dining_cost_info = activities_tools.calculate_dining_cost(
        days=days,
        travelers=travelers,
        travel_style=travel_style
    )
    
    # Lấy restaurants và dining_cost từ state nếu có (từ ActivitiesAgent)
    if 'restaurants' in state:
        restaurants = state.get('restaurants', [])
    else:
        restaurants = activities_tools.search_restaurants(destination=destination)
    
    if 'dining_cost' in state:
        dining_cost = state.get('dining_cost', 0)
    else:
        dining_cost_info = activities_tools.calculate_dining_cost(
            days=days,
            travelers=travelers,
            travel_style=travel_style
        )
        dining_cost = dining_cost_info['total_vnd']
    
    # Đảm bảo activities và activities_cost đã được set
    if not activities:
        activities = state.get('activities', [])
    if activities_cost == 0:
        activities_cost = state.get('activities_cost', 0)
        # Nếu vẫn là 0, tính lại
        if activities_cost == 0 and activities:
            activities_cost = activities_tools.calculate_activity_cost(
                activities=activities,
                travelers=travelers
            )
    
    print(f"\n🎯 Hoạt động: Tìm thấy {len(activities)} hoạt động")
    if activities:
        print(f"\n📋 Top 5 hoạt động:")
        for i, activity in enumerate(activities[:5], 1):
            print(f"\n{i}. {activity.get('name', 'Unknown')}")
            print(f"   📝 {activity.get('description', '')[:100]}...")
            print(f"   💰 {activity.get('price_per_person', 0):,} VNĐ/người")
    
    print(f"\n✅ Chi phí hoạt động: {activities_cost:,} VNĐ")
    
    print(f"\n🍽️  Nhà hàng: Tìm thấy {len(restaurants)} nhà hàng")
    if restaurants:
        print(f"\n📋 Top 5 nhà hàng:")
        for i, restaurant in enumerate(restaurants[:5], 1):
            print(f"\n{i}. {restaurant.get('name', 'Unknown')}")
            print(f"   ⭐ Rating: {restaurant.get('rating', 0)}/5")
            print(f"   💰 Price level: {restaurant.get('price_range', 'N/A')}")
    
    print(f"\n✅ Chi phí ăn uống: {dining_cost:,} VNĐ")
    print(f"   ({dining_cost/days/travelers:,} VNĐ/người/ngày)")
    
    # ==========================================
    # 5. TOTAL BUDGET
    # ==========================================
    print_section("5. TỔNG KẾT CHI PHÍ")
    
    budget_agent = BudgetAgent()
    state = {
        'transport_cost': transport_cost,
        'accommodation_cost': accommodation_cost,
        'activities_cost': activities_cost,
        'dining_cost': dining_cost,
        'days': days,
        'travelers': travelers,
        'travel_style': travel_style
    }
    
    state = await budget_agent.execute(state)
    budget = state.get('budget', {})
    
    breakdown = budget.get('breakdown', {})
    total = budget.get('total_vnd', 0)
    
    print(f"\n💰 CHI TIẾT CHI PHÍ:")
    print(f"   🚗 Di chuyển:     {breakdown.get('transport', 0):,} VNĐ")
    print(f"   🏨 Lưu trú:       {breakdown.get('accommodation', 0):,} VNĐ")
    print(f"   🎯 Hoạt động:     {breakdown.get('activities', 0):,} VNĐ")
    print(f"   🍽️  Ăn uống:       {breakdown.get('dining', 0):,} VNĐ")
    print(f"   📦 Khác:          {breakdown.get('misc', 0):,} VNĐ")
    print(f"   {'─'*50}")
    print(f"   💵 TỔNG CỘNG:     {total:,} VNĐ")
    print(f"\n   💰/người:        {total/travelers:,.0f} VNĐ")
    print(f"   💰/người/ngày:    {total/travelers/days:,.0f} VNĐ")
    
    # Phân bổ %
    allocation = budget.get('budget_allocation', {}).get('allocation_percent', {})
    if allocation:
        print(f"\n📊 PHÂN BỔ NGÂN SÁCH:")
        for key, percent in allocation.items():
            print(f"   {key.capitalize()}: {percent}%")
    
    # ==========================================
    # 6. RECOMMENDATIONS
    # ==========================================
    print_section("6. ĐỀ XUẤT")
    
    recommendations = budget.get('budget_allocation', {}).get('recommendations', [])
    if recommendations:
        print("\n💡 Gợi ý:")
        for rec in recommendations:
            print(f"   - {rec}")
    else:
        print("\n✅ Phân bổ ngân sách hợp lý!")
    
    print(f"\n💑 Phong cách lãng mạn:")
    print(f"   - Ưu tiên khách sạn/resort cao cấp")
    print(f"   - Nhà hàng lãng mạn, fine dining")
    print(f"   - Hoạt động riêng tư, không gian yên tĩnh")
    print(f"   - Chi phí cao hơn phong cách standard (~1.75x)")
    
    print_section("KẾT THÚC TEST")
    print(f"\n✅ Test hoàn tất!")
    print(f"📊 Tổng chi phí: {total:,} VNĐ cho {travelers} người trong {days} ngày")
    print(f"📍 Từ {origin} đến {destination}")

if __name__ == '__main__':
    asyncio.run(test_travel_cost())

