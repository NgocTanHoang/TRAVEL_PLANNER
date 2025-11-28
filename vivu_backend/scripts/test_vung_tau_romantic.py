"""
Test Script: TPHCM → Vũng Tàu (Romantic, 3 người, 2 ngày)
==========================================================
Test tạo lịch trình lãng mạn từ TPHCM đến Vũng Tàu
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime, timedelta
import json
import requests

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

# Override ALLOWED_HOSTS for testing
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']  # Allow all hosts for testing

from django.test import Client
from rest_framework.test import APIClient
from django.urls import reverse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_vung_tau_romantic():
    """Test Case: Romantic trip from TPHCM to Vũng Tàu (3 people, 2 days)"""
    
    print("\n" + "="*80)
    print("TEST CASE: TPHCM → Vũng Tàu (Romantic, 3 người, 2 ngày)")
    print("="*80)
    
    # Test payload
    start_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    payload = {
        "origin": "Thành phố Hồ Chí Minh",
        "destination": "Vũng Tàu",
        "start_date": start_date,
        "days": 2,
        "travelers": 3,
        "rooms": 1,
        "travel_style": "romantic",
        "interests": ["lãng mạn", "biển", "ẩm thực"]
    }
    
    # Use Django REST Framework test client (bypasses CSRF)
    client = APIClient()
    
    print(f"\n[Origin] {payload['origin']}")
    print(f"[Destination] {payload['destination']}")
    print(f"[Start date] {payload['start_date']}")
    print(f"[Days] {payload['days']}")
    print(f"[Travelers] {payload['travelers']}")
    print(f"[Travel style] {payload['travel_style']}")
    print(f"[Interests] {', '.join(payload['interests'])}")
    
    # Test: POST full plan creation
    print("\n" + "-"*80)
    print("TEST: POST /api/v1/travel-plans/ (Full Plan Creation)")
    print("-"*80)
    
    response = client.post(
        '/api/v1/travel-plans/',
        payload,
        format='json'  # DRF test client format
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = json.loads(response.content)
        print(f"[OK] Status: {data.get('status')}")
        
        # Check costs
        if 'costs' in data:
            costs = data['costs']
            print(f"\n[Cost Breakdown]")
            print(f"   - Transport: {costs.get('transport', 0):,} VNĐ")
            print(f"   - Accommodation: {costs.get('accommodation', 0):,} VNĐ")
            print(f"   - Activities: {costs.get('activities', 0):,} VNĐ")
            print(f"   - Dining: {costs.get('dining', 0):,} VNĐ")
            print(f"   - Total: {costs.get('total', 0):,} VNĐ")
        
        # Check plan details
        if 'plan' in data:
            plan = data['plan']
            
            # Transport
            if 'transport' in plan and plan['transport']:
                transport = plan['transport']
                print(f"\n[Transport]")
                print(f"   - Method: {transport.get('suggested_method', 'N/A')}")
                print(f"   - Distance: {transport.get('distance_km', 0):.1f} km")
                print(f"   - Duration: {transport.get('duration_minutes', 0):.1f} minutes")
            
            # Hotels
            if 'hotels' in plan and plan['hotels']:
                hotels = plan['hotels']
                print(f"\n[Hotels Found] {len(hotels)} options")
                if hotels:
                    selected = plan.get('selected_hotel') or hotels[0]
                    print(f"   - Selected: {selected.get('name', 'N/A')}")
                    print(f"   - Price: {selected.get('price_per_night', 0):,} VNĐ/đêm")
            
            # Activities
            if 'activities' in plan and plan['activities']:
                activities = plan['activities']
                print(f"\n[Activities Found] {len(activities)} activities")
                for i, activity in enumerate(activities[:5], 1):  # Show first 5
                    print(f"   {i}. {activity.get('name', 'N/A')} - {activity.get('type', 'N/A')}")
            
            # Restaurants
            if 'restaurants' in plan and plan['restaurants']:
                restaurants = plan['restaurants']
                print(f"\n[Restaurants Found] {len(restaurants)} restaurants")
                for i, restaurant in enumerate(restaurants[:5], 1):  # Show first 5
                    print(f"   {i}. {restaurant.get('name', 'N/A')} - {restaurant.get('cuisine', 'N/A')}")
            
            # Itinerary
            if 'itinerary' in plan:
                itinerary = plan['itinerary']
                if isinstance(itinerary, dict) and 'itinerary' in itinerary:
                    daily_schedules = itinerary['itinerary']
                    print(f"\n[Itinerary]")
                    print(f"   - Number of daily schedules: {len(daily_schedules)}")
                    print(f"   - Expected: {payload['days']}")
                    
                    for day_num, schedule in enumerate(daily_schedules, 1):
                        print(f"\n   [Day {day_num}]")
                        date = schedule.get('date', 'N/A')
                        print(f"      Date: {date}")
                        
                        activities = schedule.get('activities', [])
                        if activities:
                            print(f"      Activities: {len(activities)}")
                            for activity in activities[:3]:  # Show first 3
                                activity_data = activity.get('activity', {}) if isinstance(activity, dict) else activity
                                print(f"         - {activity_data.get('name', 'N/A')} ({activity_data.get('time', 'N/A')})")
                        
                        restaurants = schedule.get('restaurants', [])
                        if restaurants:
                            print(f"      Restaurants: {len(restaurants)}")
                            for restaurant in restaurants[:2]:  # Show first 2
                                restaurant_data = restaurant.get('restaurant', {}) if isinstance(restaurant, dict) else restaurant
                                print(f"         - {restaurant_data.get('name', 'N/A')} ({restaurant_data.get('meal_type', 'N/A')})")
        
        # Save full response to file
        output_file = PROJECT_ROOT / 'test_output_vung_tau_romantic.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Full response saved to: {output_file}")
        
    else:
        print(f"[ERROR] Status: {response.status_code}")
        try:
            error_data = json.loads(response.content)
            print(f"[ERROR] Details: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"[ERROR] Response: {response.content.decode()}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_vung_tau_romantic()






