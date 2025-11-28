"""
Test script để kiểm tra tạo lịch trình
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

# Setup Django - chạy từ thư mục vivu_backend
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from agents.travel_agents.orchestrator_agent import OrchestratorAgent
from agents.state import TravelPlanningState


async def test_create_itinerary():
    """Test tạo lịch trình với dữ liệu mẫu"""
    
    # Test case 1: Địa điểm có nhiều dữ liệu (Hà Nội)
    print("=" * 80)
    print("TEST 1: Tạo lịch trình cho Hà Nội (3 ngày)")
    print("=" * 80)
    
    state: TravelPlanningState = {
        'origin': 'Thành phố Hồ Chí Minh',
        'destination': 'Thành phố Hà Nội',
        'start_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'days': 3,
        'travelers': 2,
        'travel_style': 'standard',
        'rooms': 1,
        'interests': []
    }
    
    orchestrator = OrchestratorAgent()
    
    try:
        result_state = await orchestrator.execute(state)
        
        print("\n✅ Kết quả:")
        print(f"Status: {result_state.get('status')}")
        print(f"Destination: {result_state.get('destination')}")
        print(f"Days: {result_state.get('days')}")
        
        # Kiểm tra activities
        activities = result_state.get('activities', [])
        print(f"\n📌 Activities ({len(activities)}):")
        for i, act in enumerate(activities[:5], 1):
            name = act.get('name', 'N/A')
            print(f"  {i}. {name[:80]}{'...' if len(name) > 80 else ''}")
        
        # Kiểm tra restaurants
        restaurants = result_state.get('restaurants', [])
        print(f"\n🍽️ Restaurants ({len(restaurants)}):")
        for i, rest in enumerate(restaurants[:5], 1):
            name = rest.get('name', 'N/A')
            print(f"  {i}. {name[:80]}{'...' if len(name) > 80 else ''}")
        
        # Kiểm tra itinerary
        itinerary = result_state.get('itinerary', {})
        if itinerary:
            print(f"\n📅 Itinerary:")
            print(f"  Total days: {itinerary.get('total_days', 'N/A')}")
            # itinerary.itinerary là list các daily schedules
            daily_schedules = itinerary.get('itinerary', [])
            print(f"  Daily schedules: {len(daily_schedules)}")
            
            if len(daily_schedules) == 0:
                print("  ⚠️ WARNING: Không có daily schedules!")
                print(f"  Itinerary keys: {list(itinerary.keys())}")
            
            for day_schedule in daily_schedules[:2]:  # Chỉ hiển thị 2 ngày đầu
                day = day_schedule.get('day', 'N/A')
                date = day_schedule.get('date', 'N/A')
                theme = day_schedule.get('theme', 'N/A')
                print(f"\n  Ngày {day} ({date}): {theme}")
                
                timeline = day_schedule.get('timeline', [])
                print(f"    Timeline items: {len(timeline)}")
                for item in timeline[:3]:  # Chỉ hiển thị 3 items đầu
                    time = item.get('time', 'N/A')
                    activity = item.get('activity', 'N/A')
                    activity_short = activity[:60] + '...' if len(activity) > 60 else activity
                    print(f"      {time}: {activity_short}")
        
        # Kiểm tra costs
        print(f"\n💰 Costs:")
        print(f"  Transport: {result_state.get('transport_cost', 0):,} VNĐ")
        print(f"  Accommodation: {result_state.get('accommodation_cost', 0):,} VNĐ")
        print(f"  Activities: {result_state.get('activities_cost', 0):,} VNĐ")
        print(f"  Dining: {result_state.get('dining_cost', 0):,} VNĐ")
        print(f"  Total: {result_state.get('total_budget', 0):,} VNĐ")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Test case 2: Địa điểm ít dữ liệu (Xã Kim Trung)
    print("\n" + "=" * 80)
    print("TEST 2: Tạo lịch trình cho Xã Kim Trung (2 ngày) - Test case có vấn đề")
    print("=" * 80)
    
    state2: TravelPlanningState = {
        'origin': 'Tỉnh Bà Rịa-Vũng Tàu',
        'destination': 'Xã Kim Trung Huyện Hưng Hà Tỉnh Thái Bình Xã Kim Chung,Huyện Hưng Hà,Tỉnh Thái Bình',
        'start_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'days': 2,
        'travelers': 4,
        'travel_style': 'family',
        'rooms': 1,
        'interests': []
    }
    
    try:
        result_state2 = await orchestrator.execute(state2)
        
        print("\n✅ Kết quả:")
        print(f"Status: {result_state2.get('status')}")
        print(f"Destination: {result_state2.get('destination')}")
        print(f"Days: {result_state2.get('days')}")
        
        # Kiểm tra activities
        activities2 = result_state2.get('activities', [])
        print(f"\n📌 Activities ({len(activities2)}):")
        for i, act in enumerate(activities2[:10], 1):
            name = act.get('name', 'N/A')
            print(f"  {i}. {name[:100]}{'...' if len(name) > 100 else ''}")
        
        # Kiểm tra restaurants
        restaurants2 = result_state2.get('restaurants', [])
        print(f"\n🍽️ Restaurants ({len(restaurants2)}):")
        for i, rest in enumerate(restaurants2[:10], 1):
            name = rest.get('name', 'N/A')
            print(f"  {i}. {name[:100]}{'...' if len(name) > 100 else ''}")
        
        # Kiểm tra itinerary
        itinerary2 = result_state2.get('itinerary', {})
        if itinerary2:
            print(f"\n📅 Itinerary:")
            print(f"  Total days: {itinerary2.get('total_days', 'N/A')}")
            # itinerary.itinerary là list các daily schedules
            daily_schedules2 = itinerary2.get('itinerary', [])
            print(f"  Daily schedules: {len(daily_schedules2)}")
            
            if len(daily_schedules2) == 0:
                print("  ⚠️ WARNING: Không có daily schedules!")
                print(f"  Itinerary keys: {list(itinerary2.keys())}")
            
            for day_schedule in daily_schedules2:
                day = day_schedule.get('day', 'N/A')
                date = day_schedule.get('date', 'N/A')
                theme = day_schedule.get('theme', 'N/A')
                summary = day_schedule.get('summary', 'N/A')
                print(f"\n  Ngày {day} ({date}): {theme}")
                print(f"    Summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")
                
                timeline = day_schedule.get('timeline', [])
                print(f"    Timeline items: {len(timeline)}")
                for item in timeline:
                    time = item.get('time', 'N/A')
                    activity = item.get('activity', 'N/A')
                    activity_short = activity[:80] + '...' if len(activity) > 80 else activity
                    print(f"      {time}: {activity_short}")
        
        # Kiểm tra costs
        print(f"\n💰 Costs:")
        print(f"  Transport: {result_state2.get('transport_cost', 0):,} VNĐ")
        print(f"  Accommodation: {result_state2.get('accommodation_cost', 0):,} VNĐ")
        print(f"  Activities: {result_state2.get('activities_cost', 0):,} VNĐ")
        print(f"  Dining: {result_state2.get('dining_cost', 0):,} VNĐ")
        print(f"  Total: {result_state2.get('total_budget', 0):,} VNĐ")
        
        # Kiểm tra vấn đề
        print(f"\n🔍 Phân tích vấn đề:")
        if len(activities2) == 0:
            print("  ❌ Không có activities nào được tìm thấy")
        else:
            # Kiểm tra xem có activities nào có tên giống destination không
            dest = result_state2.get('destination', '').lower()
            duplicate_count = 0
            for act in activities2:
                if act.get('name', '').lower() == dest or len(act.get('name', '')) > 100:
                    duplicate_count += 1
            if duplicate_count > 0:
                print(f"  ⚠️ Có {duplicate_count} activities có tên giống destination hoặc quá dài")
        
        if len(restaurants2) == 0:
            print("  ❌ Không có restaurants nào được tìm thấy")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_create_itinerary())

