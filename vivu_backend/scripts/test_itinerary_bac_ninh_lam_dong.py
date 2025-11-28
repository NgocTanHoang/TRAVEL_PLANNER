"""
Test tạo lịch trình từ Bắc Ninh đến Lâm Đồng
"""
import os
import sys
import django
import asyncio
import json
from datetime import datetime, timedelta

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup Django
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from agents.travel_agents.orchestrator_agent import OrchestratorAgent
from agents.state import TravelPlanningState


async def test_bac_ninh_to_lam_dong():
    """Test tạo lịch trình từ Bắc Ninh đến Lâm Đồng"""
    
    print("=" * 80)
    print("TEST: TẠO LỊCH TRÌNH TỪ BẮC NINH ĐẾN LÂM ĐỒNG")
    print("=" * 80)
    
    state: TravelPlanningState = {
        'origin': 'Tỉnh Bắc Ninh',
        'destination': 'Tỉnh Lâm Đồng',
        'start_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'days': 4,
        'travelers': 2,
        'travel_style': 'standard',
        'rooms': 1,
        'interests': []
    }
    
    print(f"\n📋 Thông tin chuyến đi:")
    print(f"  Điểm đi: {state['origin']}")
    print(f"  Điểm đến: {state['destination']}")
    print(f"  Ngày bắt đầu: {state['start_date']}")
    print(f"  Số ngày: {state['days']}")
    print(f"  Số người: {state['travelers']}")
    print(f"  Phong cách: {state['travel_style']}")
    
    orchestrator = OrchestratorAgent()
    
    try:
        print(f"\n⏳ Đang tạo lịch trình...")
        result_state = await orchestrator.execute(state)
        
        print(f"\n✅ Kết quả:")
        print(f"Status: {result_state.get('status')}")
        print(f"Destination: {result_state.get('destination')}")
        print(f"Days: {result_state.get('days')}")
        
        # Kiểm tra transport
        transport = result_state.get('transport', {})
        if transport:
            print(f"\n🚗 Phương tiện di chuyển:")
            print(f"  Phương thức: {transport.get('method', 'N/A')}")
            print(f"  Khoảng cách: {transport.get('distance_km', 0):.2f} km")
            print(f"  Thời gian: {transport.get('duration_hours', 0):.2f} giờ")
        
        # Kiểm tra activities
        activities = result_state.get('activities', [])
        print(f"\n📌 Activities ({len(activities)}):")
        for i, act in enumerate(activities[:10], 1):
            name = act.get('name', 'N/A')
            price = act.get('price_per_person', act.get('price', 0))
            source = act.get('source', 'N/A')
            print(f"  {i:2d}. {name[:70]}{'...' if len(name) > 70 else ''}")
            print(f"      Giá: {price:,.0f} VNĐ/người | Nguồn: {source}")
        
        # Kiểm tra restaurants
        restaurants = result_state.get('restaurants', [])
        print(f"\n🍽️ Restaurants ({len(restaurants)}):")
        for i, rest in enumerate(restaurants[:10], 1):
            name = rest.get('name', 'N/A')
            rating = rest.get('rating', 0)
            print(f"  {i:2d}. {name[:70]}{'...' if len(name) > 70 else ''}")
            if rating:
                print(f"      Rating: {rating}/5")
        
        # Kiểm tra hotels
        hotels = result_state.get('hotels', [])
        print(f"\n🏨 Hotels ({len(hotels)}):")
        for i, hotel in enumerate(hotels[:5], 1):
            name = hotel.get('name', 'N/A')
            price = hotel.get('price_per_night', 0)
            stars = hotel.get('stars', 0)
            print(f"  {i:2d}. {name[:70]}{'...' if len(name) > 70 else ''}")
            if price:
                print(f"      Giá: {price:,.0f} VNĐ/đêm | {stars} sao")
        
        # Kiểm tra itinerary
        itinerary = result_state.get('itinerary', {})
        if itinerary:
            print(f"\n📅 Itinerary:")
            print(f"  Total days: {itinerary.get('total_days', 'N/A')}")
            daily_schedules = itinerary.get('itinerary', [])
            print(f"  Daily schedules: {len(daily_schedules)}")
            
            for day_schedule in daily_schedules:
                day = day_schedule.get('day', 'N/A')
                date = day_schedule.get('date', 'N/A')
                theme = day_schedule.get('theme', 'N/A')
                summary = day_schedule.get('summary', 'N/A')
                print(f"\n  📆 Ngày {day} ({date}): {theme}")
                print(f"     {summary[:100]}{'...' if len(summary) > 100 else ''}")
                
                timeline = day_schedule.get('timeline', [])
                print(f"     Timeline items: {len(timeline)}")
                for item in timeline[:5]:  # Chỉ hiển thị 5 items đầu
                    time = item.get('time', 'N/A')
                    activity = item.get('activity', 'N/A')
                    activity_short = activity[:60] + '...' if len(activity) > 60 else activity
                    print(f"       {time}: {activity_short}")
                if len(timeline) > 5:
                    print(f"       ... và {len(timeline) - 5} hoạt động khác")
        
        # Kiểm tra costs
        print(f"\n💰 Costs:")
        print(f"  Transport: {result_state.get('transport_cost', 0):,} VNĐ")
        print(f"  Accommodation: {result_state.get('accommodation_cost', 0):,} VNĐ")
        print(f"  Activities: {result_state.get('activities_cost', 0):,} VNĐ")
        print(f"  Dining: {result_state.get('dining_cost', 0):,} VNĐ")
        
        budget = result_state.get('budget', {})
        if budget:
            total = budget.get('total_vnd', 0)
            print(f"  Total: {total:,} VNĐ")
            if total > 0:
                per_person = budget.get('per_person', 0)
                per_day = budget.get('per_day', 0)
                print(f"  /người: {per_person:,} VNĐ")
                print(f"  /ngày: {per_day:,} VNĐ")
        
        # Kiểm tra itinerary description
        itinerary_description = result_state.get('itinerary_description', '')
        if itinerary_description:
            print(f"\n📝 Mô tả lịch trình:")
            print(f"  {itinerary_description[:200]}{'...' if len(itinerary_description) > 200 else ''}")
        
        print(f"\n" + "=" * 80)
        print("✅ Hoàn thành!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_bac_ninh_to_lam_dong())

