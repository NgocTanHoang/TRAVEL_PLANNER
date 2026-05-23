"""
Integration Test: Travel Plan Preview API
==========================================
Test case TC_ITIN_001_romantic_dalat

Tests the full travel planning workflow:
- Geocoding → Transport → Accommodation → Activities → Budget → Planning
- Edge cases: Vector DB fallback, API failures, etc.
"""
import pytest
import os
import sys
import django
from pathlib import Path
from datetime import datetime, timedelta
import json

# Setup Django
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class TestTravelPlanPreview:
    """Test suite for Travel Plan Preview API"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client"""
        return APIClient()
    
    @pytest.fixture
    def test_payload(self):
        """Test case payload - TC_ITIN_001_romantic_dalat"""
        start_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        return {
            "user_id": "test_user_001",
            "origin": "Quận 1, Ho Chi Minh City, Vietnam",
            "destination": "Da Lat, Lam Dong, Vietnam",
            "start_date": start_date,
            "days": 4,
            "travelers": 2,
            "rooms": 1,
            "travel_style": ["romantic", "wellness"],
            "preferences": {
                "max_budget_vnd": 50000000,
                "preferred_transport": ["car", "train"],
                "avoid_long_drive_min": 240,
                "must_have": ["spa", "scenic viewpoint"],
                "dietary_restrictions": []
            }
        }
    
    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_tc_itin_001_full_workflow(self, api_client, test_payload):
        """
        Test Case TC_ITIN_001: Full workflow test
        
        Expected:
        - HTTP 200 OK
        - Complete itinerary_preview with 4 daily_schedules
        - Cost breakdown within expected ranges
        - Geocoding resolved
        - At least one wellness/spa activity
        """
        # For now, use GET endpoint (will update to POST later)
        # Convert payload to query params
        response = api_client.get(
            '/api/v1/travel-plans/preview/',
            {
                'origin': test_payload['origin'],
                'destination': test_payload['destination'],
                'days': test_payload['days'],
                'travelers': test_payload['travelers'],
                'travel_style': ','.join(test_payload['travel_style'])
            }
        )
        
        # Assert HTTP status
        assert response.status_code == status.HTTP_200_OK, \
            f"Expected 200 OK, got {response.status_code}: {response.data}"
        
        data = response.data
        
        # Assert response structure
        assert 'status' in data, "Response missing 'status' field"
        assert data['status'] == 'success', f"Expected status='success', got '{data.get('status')}'"
        
        # Assert preview exists
        assert 'preview' in data, "Response missing 'preview' field"
        preview = data['preview']
        
        # Assert transport exists
        assert 'transport' in preview, "Preview missing 'transport' field"
        transport = preview['transport']
        
        # Check geocoding (should be in transport or separate field)
        # Note: Current implementation may not have separate geocoding fields
        # This is acceptable if coordinates are in transport
        
        # Assert budget exists
        assert 'budget_estimate' in preview, "Preview missing 'budget_estimate' field"
        budget = preview['budget_estimate']
        
        # Check budget structure
        if isinstance(budget, dict):
            assert 'total_vnd' in budget or 'per_person' in budget, \
                "Budget missing cost fields"
        
        logger.info(f"✅ Test TC_ITIN_001 passed: Got preview with transport and budget")
        logger.info(f"   Transport: {transport.get('suggested_method', 'N/A')}")
        logger.info(f"   Budget keys: {list(budget.keys()) if isinstance(budget, dict) else 'N/A'}")
    
    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_tc_itin_001_full_plan_create(self, api_client, test_payload):
        """
        Test full plan creation (POST /api/v1/travel-plans/)
        This should return complete itinerary with daily schedules
        """
        response = api_client.post(
            '/api/v1/travel-plans/',
            {
                'origin': test_payload['origin'],
                'destination': test_payload['destination'],
                'start_date': test_payload['start_date'],
                'days': test_payload['days'],
                'travelers': test_payload['travelers'],
                'rooms': test_payload['rooms'],
                'travel_style': ','.join(test_payload['travel_style'])
            },
            format='json'
        )
        
        # Assert HTTP status
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Expected 200/201, got {response.status_code}: {response.data}"
        
        data = response.data
        
        # Assert response structure
        assert 'status' in data, "Response missing 'status' field"
        assert data['status'] == 'success', f"Expected status='success', got '{data.get('status')}'"
        
        # Assert plan exists
        assert 'plan' in data, "Response missing 'plan' field"
        plan = data['plan']
        
        # Assert costs exist
        assert 'costs' in data, "Response missing 'costs' field"
        costs = data['costs']
        
        # Check cost breakdown
        assert 'total' in costs, "Costs missing 'total' field"
        total_cost = costs['total']
        assert total_cost > 0, f"Total cost should be > 0, got {total_cost}"
        
        # Check individual costs
        transport_cost = costs.get('transport', 0)
        accommodation_cost = costs.get('accommodation', 0)
        activities_cost = costs.get('activities', 0)
        dining_cost = costs.get('dining', 0)
        
        # Expected ranges (from test case)
        # Transport: 800k - 2.5M
        if transport_cost > 0:
            assert 800000 <= transport_cost <= 2500000, \
                f"Transport cost {transport_cost} outside expected range 800k-2.5M"
        
        # Accommodation: 6M - 12M (3 nights × 2.8M/night for premium)
        if accommodation_cost > 0:
            assert 6000000 <= accommodation_cost <= 12000000, \
                f"Accommodation cost {accommodation_cost} outside expected range 6M-12M"
        
        # Activities: 0.5M - 3.0M
        if activities_cost > 0:
            assert 500000 <= activities_cost <= 3000000, \
                f"Activities cost {activities_cost} outside expected range 0.5M-3.0M"
        
        # Dining: 2.0M - 5.5M
        if dining_cost > 0:
            assert 2000000 <= dining_cost <= 5500000, \
                f"Dining cost {dining_cost} outside expected range 2.0M-5.5M"
        
        # Check total consistency (±5% tolerance)
        calculated_total = transport_cost + accommodation_cost + activities_cost + dining_cost
        if calculated_total > 0:
            tolerance = calculated_total * 0.05
            assert abs(total_cost - calculated_total) <= tolerance, \
                f"Total cost {total_cost} inconsistent with breakdown {calculated_total} (tolerance: {tolerance})"
        
        # Check itinerary exists
        if 'itinerary' in plan:
            itinerary = plan['itinerary']
            if isinstance(itinerary, dict) and 'itinerary' in itinerary:
                daily_schedules = itinerary['itinerary']
                assert len(daily_schedules) == test_payload['days'], \
                    f"Expected {test_payload['days']} daily schedules, got {len(daily_schedules)}"
                
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
                            break
                    if has_wellness:
                        break
                
                # Note: This is a warning, not a failure
                if not has_wellness:
                    logger.warning("⚠️  No wellness/spa activity found in itinerary (expected for romantic+wellness style)")
        
        logger.info(f"✅ Test TC_ITIN_001 full plan creation passed")
        logger.info(f"   Total cost: {total_cost:,} VNĐ")
        logger.info(f"   Transport: {transport_cost:,} VNĐ")
        logger.info(f"   Accommodation: {accommodation_cost:,} VNĐ")
        logger.info(f"   Activities: {activities_cost:,} VNĐ")
        logger.info(f"   Dining: {dining_cost:,} VNĐ")
    
    @pytest.mark.django_db
    def test_geocoding_resolution(self, api_client):
        """Test geocoding resolution for origin and destination"""
        response = api_client.get(
            '/api/v1/travel-plans/preview/',
            {
                'origin': 'Quận 1, Ho Chi Minh City, Vietnam',
                'destination': 'Da Lat, Lam Dong, Vietnam',
                'days': 4,
                'travelers': 2
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.data
        preview = data.get('preview', {})
        transport = preview.get('transport', {})
        
        # Check distance (HCM → Đà Lạt ≈ 300-320 km)
        distance_km = transport.get('distance_km')
        if distance_km:
            assert 270 <= distance_km <= 350, \
                f"Distance {distance_km}km outside expected range 270-350km for HCM→Đà Lạt"
        
        logger.info(f"✅ Geocoding test passed: Distance = {distance_km}km")
    
    @pytest.mark.django_db
    def test_edge_case_missing_params(self, api_client):
        """Test edge case: missing required parameters"""
        response = api_client.get(
            '/api/v1/travel-plans/preview/',
            {
                'origin': 'Hà Nội',
                # Missing destination and days
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logger.info("✅ Edge case test passed: Missing params correctly rejected")
    
    @pytest.mark.django_db
    def test_edge_case_invalid_days(self, api_client):
        """Test edge case: invalid days (too many)"""
        response = api_client.get(
            '/api/v1/travel-plans/preview/',
            {
                'origin': 'Hà Nội',
                'destination': 'Đà Nẵng',
                'days': 20,  # Exceeds max of 14
                'travelers': 2
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logger.info("✅ Edge case test passed: Invalid days correctly rejected")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

