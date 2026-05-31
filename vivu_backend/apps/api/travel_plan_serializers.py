"""
Serializers for Travel Planning API với 7 Agents
================================================
"""
from rest_framework import serializers
from typing import Optional, List, Dict, Any


class TravelPlanRequestSerializer(serializers.Serializer):
    """Request serializer cho travel planning"""
    origin = serializers.CharField(required=True, help_text="Điểm xuất phát")
    destination = serializers.CharField(required=True, help_text="Điểm đến")
    start_date = serializers.DateField(required=True, help_text="Ngày bắt đầu (YYYY-MM-DD)")
    days = serializers.IntegerField(required=True, min_value=1, max_value=14, help_text="Số ngày (tối đa 14 ngày)")
    travelers = serializers.IntegerField(required=True, min_value=1, max_value=20, help_text="Số người")
    travel_style = serializers.CharField(
        default='standard',
        help_text="Phong cách du lịch (string hoặc JSON array cho multiple styles). Ví dụ: 'budget', 'gastronomy', hoặc '[\"romantic\", \"luxury\"]'"
    )
    budget = serializers.FloatField(required=False, min_value=0, help_text="Ngân sách tối đa (VNĐ)")
    rooms = serializers.IntegerField(default=1, min_value=1, max_value=10, help_text="Số phòng")
    interests = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Sở thích du lịch"
    )
    selected_hotel = serializers.DictField(required=False, help_text="Khách sạn đã chọn")


class TravelPlanPreviewQuerySerializer(serializers.Serializer):
    """Query serializer cho preview travel plan."""

    origin = serializers.CharField(required=True, help_text="Điểm xuất phát")
    destination = serializers.CharField(required=True, help_text="Điểm đến")
    days = serializers.IntegerField(required=True, min_value=1, max_value=14, help_text="Số ngày")
    travelers = serializers.IntegerField(required=False, default=2, min_value=1, max_value=20, help_text="Số người")
    travel_style = serializers.CharField(required=False, default='standard', help_text="Phong cách du lịch")


class Step2TravelInfoSerializer(serializers.Serializer):
    """Request serializer cho Step 2."""

    origin = serializers.CharField(required=True, help_text="Điểm xuất phát")
    destination = serializers.CharField(required=True, help_text="Điểm đến")
    start_date = serializers.DateField(required=True, help_text="Ngày bắt đầu (YYYY-MM-DD)")
    days = serializers.IntegerField(required=True, min_value=1, max_value=14, help_text="Số ngày")
    travelers = serializers.IntegerField(required=True, min_value=1, max_value=20, help_text="Số người")


class Step3BudgetSuggestionSerializer(Step2TravelInfoSerializer):
    """Request serializer cho Step 3."""

    travel_style = serializers.CharField(required=False, default='standard', help_text="Phong cách du lịch")
    rooms = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10, help_text="Số phòng")
    selected_transport = serializers.DictField(required=False, help_text="Phương tiện đã chọn")


class Step4ConfirmPlanSerializer(Step3BudgetSuggestionSerializer):
    """Request serializer cho Step 4 plan generation."""

    selected_hotel = serializers.DictField(required=False, help_text="Khách sạn đã chọn")
    interests = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Sở thích du lịch"
    )
    budget = serializers.JSONField(required=False, help_text="Ngân sách hoặc breakdown từ client")


class TransportSerializer(serializers.Serializer):
    """Transport information"""
    origin = serializers.CharField()
    destination = serializers.CharField()
    distance_km = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    suggested_method = serializers.CharField()
    estimated_cost_vnd = serializers.FloatField(required=False, allow_null=True)


class FlightSerializer(serializers.Serializer):
    """Flight information"""
    price_vnd = serializers.FloatField()
    currency = serializers.CharField()
    route_type = serializers.CharField()
    origin_iata = serializers.CharField()
    destination_iata = serializers.CharField()
    passengers = serializers.IntegerField()
    source = serializers.CharField()


class HotelSerializer(serializers.Serializer):
    """Hotel information"""
    name = serializers.CharField()
    price_per_night = serializers.FloatField()
    stars = serializers.IntegerField(required=False, allow_null=True)
    rating = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField()


class ActivitySerializer(serializers.Serializer):
    """Activity information"""
    name = serializers.CharField()
    type = serializers.CharField(required=False)
    price_per_person = serializers.FloatField(required=False, allow_null=True)
    duration_hours = serializers.FloatField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)


class RestaurantSerializer(serializers.Serializer):
    """Restaurant information"""
    name = serializers.CharField()
    cuisine = serializers.CharField(required=False, allow_null=True)
    price_range = serializers.CharField(required=False, allow_null=True)
    rating = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)


class BudgetSerializer(serializers.Serializer):
    """Budget breakdown"""
    total_vnd = serializers.FloatField()
    breakdown = serializers.DictField()
    per_person = serializers.FloatField()
    per_day = serializers.FloatField()
    travel_style = serializers.CharField()


class DailyScheduleSerializer(serializers.Serializer):
    """Daily schedule"""
    day = serializers.IntegerField()
    date = serializers.CharField()
    theme = serializers.CharField()
    accommodation = serializers.DictField(required=False, allow_null=True)
    meals = serializers.DictField()
    activities = serializers.ListField()
    tips = serializers.ListField()


class ItinerarySerializer(serializers.Serializer):
    """Full itinerary"""
    destination = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    total_days = serializers.IntegerField()
    itinerary = serializers.ListField(child=DailyScheduleSerializer())


class CostBreakdownSerializer(serializers.Serializer):
    """Cost breakdown"""
    transport = serializers.FloatField()
    accommodation = serializers.FloatField()
    activities = serializers.FloatField()
    dining = serializers.FloatField()
    total = serializers.FloatField()


class TravelPlanResponseSerializer(serializers.Serializer):
    """Response serializer cho travel plan"""
    status = serializers.CharField()
    plan = serializers.DictField(help_text="Kế hoạch du lịch chi tiết")
    costs = CostBreakdownSerializer()
    timestamp = serializers.DateTimeField()


class TravelPlanPreviewSerializer(serializers.Serializer):
    """Preview response"""
    status = serializers.CharField()
    preview = serializers.DictField()
    timestamp = serializers.DateTimeField()

