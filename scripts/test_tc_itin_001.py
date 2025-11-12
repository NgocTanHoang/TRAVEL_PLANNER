"""
Test Script for TC_ITIN_001_romantic_dalat
===========================================
Manual test script to verify the travel plan preview API
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


def test_tc_itin_001():
    """Test Case TC_ITIN_001: Romantic + Wellness trip to Da Lat"""
    
    print("\n" + "="*80)
    print("TEST CASE TC_ITIN_001_romantic_dalat")
    print("="*80)
    
    # Test payload
    start_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    payload = {
        "origin": "Quận 1, Ho Chi Minh City, Vietnam",
        "destination": "Da Lat, Lam Dong, Vietnam",
        "start_date": start_date,
        "days": 4,
        "travelers": 2,
        "rooms": 1,
        "travel_style": "romantic,wellness"  # Comma-separated for GET
    }
    
    # Use Django REST Framework test client (bypasses CSRF)
    client = APIClient()
    
    print(f"\n[Origin] {payload['origin']}")
    print(f"[Destination] {payload['destination']}")
    print(f"[Start date] {payload['start_date']}")
    print(f"[Days] {payload['days']}")
    print(f"[Travelers] {payload['travelers']}")
    print(f"[Travel style] {payload['travel_style']}")
    
    # Test 1: GET preview (quick preview)
    print("\n" + "-"*80)
    print("TEST 1: GET /api/v1/travel-plans/preview/ (Quick Preview)")
    print("-"*80)
    
    response = client.get('/api/v1/travel-plans/preview/', payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"[OK] Status: {data.get('status')}")
        
        if 'preview' in data:
            preview = data['preview']
            print(f"\n[Preview Data]")
            print(f"   - Transport: {bool(preview.get('transport'))}")
            print(f"   - Budget: {bool(preview.get('budget_estimate'))}")
            
            if 'transport' in preview:
                transport = preview['transport']
                print(f"\n[Transport Details]")
                print(f"   - Method: {transport.get('suggested_method', 'N/A')}")
                print(f"   - Distance: {transport.get('distance_km', 0):.1f} km")
                print(f"   - Duration: {transport.get('duration_minutes', 0):.1f} minutes")
                print(f"   - Cost: {transport.get('estimated_cost_vnd', 0):,} VNĐ")
            
            if 'budget_estimate' in preview:
                budget = preview['budget_estimate']
                if isinstance(budget, dict):
                    print(f"\n[Budget Estimate]")
                    print(f"   - Total: {budget.get('total_vnd', 0):,} VNĐ")
                    print(f"   - Per person: {budget.get('per_person', 0):,} VNĐ")
    else:
        print(f"❌ Error: {response.content.decode()}")
    
    # Test 2: POST full plan creation
    print("\n" + "-"*80)
    print("TEST 2: POST /api/v1/travel-plans/ (Full Plan Creation)")
    print("-"*80)
    
    post_payload = {
        "origin": payload['origin'],
        "destination": payload['destination'],
        "start_date": payload['start_date'],
        "days": payload['days'],
        "travelers": payload['travelers'],
        "rooms": payload['rooms'],
        "travel_style": payload['travel_style']
    }
    
    response = client.post(
        '/api/v1/travel-plans/',
        post_payload,
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
            
            # Validate cost ranges
            transport_cost = costs.get('transport', 0)
            accommodation_cost = costs.get('accommodation', 0)
            activities_cost = costs.get('activities', 0)
            dining_cost = costs.get('dining', 0)
            total_cost = costs.get('total', 0)
            
            print(f"\n[Cost Validation]")
            
            # Transport: 800k - 2.5M
            if transport_cost > 0:
                if 800000 <= transport_cost <= 2500000:
                    print(f"   [OK] Transport cost {transport_cost:,} VNĐ within range (800k-2.5M)")
                else:
                    print(f"   [WARN] Transport cost {transport_cost:,} VNĐ outside expected range (800k-2.5M)")
            
            # Accommodation: 6M - 12M
            if accommodation_cost > 0:
                if 6000000 <= accommodation_cost <= 12000000:
                    print(f"   [OK] Accommodation cost {accommodation_cost:,} VNĐ within range (6M-12M)")
                else:
                    print(f"   [WARN] Accommodation cost {accommodation_cost:,} VNĐ outside expected range (6M-12M)")
            
            # Activities: 0.5M - 3.0M
            if activities_cost > 0:
                if 500000 <= activities_cost <= 3000000:
                    print(f"   [OK] Activities cost {activities_cost:,} VNĐ within range (0.5M-3.0M)")
                else:
                    print(f"   [WARN] Activities cost {activities_cost:,} VNĐ outside expected range (0.5M-3.0M)")
            
            # Dining: 2.0M - 5.5M
            if dining_cost > 0:
                if 2000000 <= dining_cost <= 5500000:
                    print(f"   [OK] Dining cost {dining_cost:,} VNĐ within range (2.0M-5.5M)")
                else:
                    print(f"   [WARN] Dining cost {dining_cost:,} VNĐ outside expected range (2.0M-5.5M)")
            
            # Total consistency
            calculated_total = transport_cost + accommodation_cost + activities_cost + dining_cost
            if calculated_total > 0:
                tolerance = calculated_total * 0.05
                diff = abs(total_cost - calculated_total)
                if diff <= tolerance:
                    print(f"   [OK] Total cost consistent (diff: {diff:,} VNĐ, tolerance: {tolerance:,} VNĐ)")
                else:
                    print(f"   [WARN] Total cost inconsistent (diff: {diff:,} VNĐ, tolerance: {tolerance:,} VNĐ)")
        
        # Check itinerary
        if 'plan' in data:
            plan = data['plan']
            if 'itinerary' in plan:
                itinerary = plan['itinerary']
                if isinstance(itinerary, dict) and 'itinerary' in itinerary:
                    daily_schedules = itinerary['itinerary']
                    print(f"\n[Itinerary]")
                    print(f"   - Number of daily schedules: {len(daily_schedules)}")
                    print(f"   - Expected: {payload['days']}")
                    
                    if len(daily_schedules) == payload['days']:
                        print(f"   [OK] Daily schedules count matches")
                    else:
                        print(f"   [WARN] Daily schedules count mismatch")
                    
                    # Check for wellness/spa activities
                    has_wellness = False
                    for schedule in daily_schedules:
                        activities = schedule.get('activities', [])
                        for activity in activities:
                            activity_data = activity.get('activity', {}) if isinstance(activity, dict) else activity
                            activity_type = activity_data.get('type', '').lower()
                            activity_name = activity_data.get('name', '').lower()
                            if 'wellness' in activity_type or 'spa' in activity_type or \
                               'spa' in activity_name or 'wellness' in activity_name:
                                has_wellness = True
                                print(f"   [OK] Found wellness/spa activity: {activity_data.get('name', 'N/A')}")
                                break
                        if has_wellness:
                            break
                    
                    if not has_wellness:
                        print(f"   [WARN] No wellness/spa activity found (expected for romantic+wellness style)")
    else:
        print(f"[ERROR] {response.content.decode()}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_tc_itin_001()

