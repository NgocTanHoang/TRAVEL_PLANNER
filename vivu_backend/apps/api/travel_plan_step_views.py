"""
Workflow 4 Bước - API Endpoints riêng cho từng step
===================================================
Chỉ sử dụng VietMap API cho geocoding và routing
"""
import sys
import os
from pathlib import Path
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.db import IntegrityError
import logging
import asyncio
import traceback

from apps.analytics.models import YeuCauLoTrinh
from apps.analytics.services import ghi_nhan_yeu_cau_lo_trinh_async
from utils.security import ensure_sensitive_log_filter, sanitize_sensitive_string

# Add backend directory to path for agents, tools, utils, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import caching utilities
from utils.cache import cache_get, cache_set, generate_cache_key
from .travel_plan_serializers import (
    Step2TravelInfoSerializer,
    Step3BudgetSuggestionSerializer,
    Step4ConfirmPlanSerializer,
)
from .travel_plan_views import (
    _require_authenticated_request,
    _save_structured_travel_plan_for_user,
)

logger = logging.getLogger(__name__)
ensure_sensitive_log_filter(logger)


def rate_limit_check(user_id: int, limit: int = 20, window: int = 60) -> bool:
    """Check if user has exceeded rate limit"""
    cache_key = f"rate_limit:travel_step:user_{user_id}"
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return False
    
    cache.set(cache_key, count + 1, window)
    return True


class Step1LocationSelectionView(APIView):
    """
    Step 1: Chọn địa điểm và validate
    POST /api/v1/travel-plans/step1/
    
    Request:
    {
        "origin": "Thành phố Hồ Chí Minh",
        "destination": "Thành phố Hà Nội"
    }
    
    Response:
    {
        "status": "success",
        "origin": {...},
        "destination": {...},
        "distance_km": 1730.5,
        "estimated_duration": "1h 30m",
        "recommended_transport": "Máy bay"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Validate locations and calculate distance"""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            origin = request.data.get('origin', '').strip()
            destination = request.data.get('destination', '').strip()
            
            if not origin or not destination:
                return Response({
                    'error': 'Vui lòng nhập đầy đủ điểm đi và điểm đến'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Import geo tools
            from tools.geo_tools import get_geo_tools
            geo_tools = get_geo_tools()
            
            # Geocode both locations
            origin_result = geo_tools.geocode(origin)
            destination_result = geo_tools.geocode(destination)
            
            if not origin_result:
                return Response({
                    'error': f'Không tìm thấy địa điểm: {origin}',
                    'origin': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not destination_result:
                return Response({
                    'error': f'Không tìm thấy địa điểm: {destination}',
                    'destination': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate distance and time
            route_info = geo_tools.calculate_distance_time(
                origin_result['formatted_address'],
                destination_result['formatted_address']
            )
            
            if not route_info:
                return Response({
                    'error': 'Không thể tính toán khoảng cách'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Recommend transport
            distance_km = route_info.get('distance_km', 0)
            duration_minutes = route_info.get('duration_minutes', 0)
            
            if distance_km > 500:
                recommended_transport = "Máy bay"
                transport_icon = "✈️"
            elif distance_km > 200:
                recommended_transport = "Xe khách / Tàu hỏa"
                transport_icon = "🚂"
            else:
                recommended_transport = "Xe máy / Ô tô"
                transport_icon = "🚗"
            
            # Format duration
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            if hours > 0:
                estimated_duration = f"{hours}h {minutes}m"
            else:
                estimated_duration = f"{minutes}m"
            
            return Response({
                'status': 'success',
                'origin': {
                    'name': origin_result.get('formatted_address', origin),
                    'latitude': origin_result.get('latitude'),
                    'longitude': origin_result.get('longitude')
                },
                'destination': {
                    'name': destination_result.get('formatted_address', destination),
                    'latitude': destination_result.get('latitude'),
                    'longitude': destination_result.get('longitude')
                },
                'distance_km': round(distance_km, 2),
                'estimated_duration': estimated_duration,
                'recommended_transport': recommended_transport,
                'transport_icon': transport_icon
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in Step 1: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Step2TravelInfoView(APIView):
    """
    Step 2: Thông tin chuyến đi
    POST /api/v1/travel-plans/step2/
    
    Request:
    {
        "origin": "Thành phố Hồ Chí Minh",
        "destination": "Thành phố Hà Nội",
        "start_date": "2025-11-10",
        "days": 3,
        "travelers": 2
    }
    
    Response:
    {
        "status": "success",
        "transport": {...},
        "recommended_days": 3,
        "recommended_transport": "Máy bay"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Get transport options and recommendations"""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            serializer = Step2TravelInfoSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            origin = validated_data['origin']
            destination = validated_data['destination']
            start_date = validated_data['start_date'].strftime('%Y-%m-%d')
            days = validated_data['days']
            travelers = validated_data['travelers']

            # Get transport options
            from tools.transport_tools import get_transport_tools
            transport_tools = get_transport_tools()
            
            from tools.geo_tools import get_geo_tools
            geo_tools = get_geo_tools()
            
            # Geocode to get coordinates
            origin_result = geo_tools.geocode(origin)
            destination_result = geo_tools.geocode(destination)
            
            if not origin_result or not destination_result:
                return Response({
                    'error': 'Không thể xác định vị trí'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get transport options using compare_all_transport_options
            transport_options = transport_tools.compare_all_transport_options(
                origin=origin_result['formatted_address'],
                destination=destination_result['formatted_address'],
                travelers=travelers
            )
            
            # Recommend transport based on distance
            distance_km = transport_options.get('distance_km', 0)
            if distance_km > 500:
                recommended_transport = "Máy bay"
            elif distance_km > 200:
                recommended_transport = "Xe khách / Tàu hỏa"
            else:
                recommended_transport = "Xe máy / Ô tô"
            
            return Response({
                'status': 'success',
                'transport': transport_options,
                'recommended_days': days,
                'recommended_transport': recommended_transport
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in Step 2: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Step3BudgetSuggestionView(APIView):
    """
    Step 3: Đề xuất ngân sách và khách sạn
    POST /api/v1/travel-plans/step3/
    
    Request:
    {
        "origin": "Thành phố Hồ Chí Minh",
        "destination": "Thành phố Hà Nội",
        "start_date": "2025-11-10",
        "days": 3,
        "travelers": 2,
        "travel_style": "standard",
        "rooms": 1
    }
    
    Response:
    {
        "status": "success",
        "budget": {...},
        "hotels": [...]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Get budget suggestions and hotels"""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            serializer = Step3BudgetSuggestionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            origin = validated_data['origin']
            destination = validated_data['destination']
            start_date = validated_data['start_date'].strftime('%Y-%m-%d')
            days = validated_data['days']
            travelers = validated_data['travelers']
            travel_style = validated_data.get('travel_style', 'standard')
            rooms = validated_data.get('rooms', 1)

            # Get selected transport from request (if user selected in Step 2)
            selected_transport = validated_data.get('selected_transport')
            
            # Use orchestrator to get budget and hotels
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            from agents.state import TravelPlanningState
            
            orchestrator = OrchestratorAgent()
            
            # Create initial state
            state: TravelPlanningState = {
                'origin': origin,
                'destination': destination,
                'start_date': start_date,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'rooms': rooms
            }
            
            # If user selected transport in Step 2, use it
            if selected_transport:
                # Set transport cost from selected transport
                transport_cost = selected_transport.get('cost_vnd', 0)
                if transport_cost:
                    state['transport_cost'] = transport_cost
                    state['transport'] = {
                        'method': selected_transport.get('method'),
                        'method_name': selected_transport.get('method_name'),
                        'distance_km': selected_transport.get('distance_km', 0),
                        'duration_minutes': selected_transport.get('duration_minutes', 0),
                        'estimated_cost_vnd': transport_cost
                    }
            
            # Run orchestrator (only accommodation and budget agents)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result_state = loop.run_until_complete(orchestrator.execute(state))
            finally:
                loop.close()
            
            # Format response
            response_data = {
                'status': 'success',
                'budget': result_state.get('budget', {}),
                'hotels': result_state.get('hotels', []),
                'transport_cost': result_state.get('transport_cost', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in Step 3: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Step4ConfirmAndPlanView(APIView):
    """
    Step 4: Xác nhận và tạo kế hoạch đầy đủ
    POST /api/v1/travel-plans/step4/
    
    Request:
    {
        "origin": "Thành phố Hồ Chí Minh",
        "destination": "Thành phố Hà Nội",
        "start_date": "2025-11-10",
        "days": 3,
        "travelers": 2,
        "travel_style": "standard",
        "rooms": 1,
        "selected_hotel": {...},
        "budget": {...},
        "interests": []
    }
    
    Response:
    {
        "itinerary": {...},
        "costs": {...},
        "activities": [...],
        "restaurants": [...]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Create full travel plan"""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            serializer = Step4ConfirmPlanSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            origin = validated_data['origin']
            destination = validated_data['destination']
            start_date = validated_data['start_date'].strftime('%Y-%m-%d')
            days = validated_data['days']
            travelers = validated_data['travelers']
            travel_style = validated_data.get('travel_style', 'standard')
            rooms = validated_data.get('rooms', 1)
            selected_hotel = validated_data.get('selected_hotel')
            interests = validated_data.get('interests', [])
            
            # Check cache first
            cache_key = generate_cache_key('travel_step4', origin, destination, start_date, days, travelers, travel_style, rooms, str(interests))
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"Returning cached Step 4 result for {cache_key}")
                return Response(cached_result, status=status.HTTP_200_OK)
            
            # Use orchestrator to create full plan
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            from agents.state import TravelPlanningState
            
            orchestrator = OrchestratorAgent()
            
            # Normalize destination name để loại bỏ duplicate và format sai
            from agents.travel_agents.activities_agent import _normalize_destination_name_for_display
            normalized_destination = _normalize_destination_name_for_display(destination)
            
            # Create initial state
            state: TravelPlanningState = {
                'origin': origin,
                'destination': normalized_destination,
                'start_date': start_date,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'rooms': rooms,
                'selected_hotel': selected_hotel,
                'interests': interests
            }
            
            # Run orchestrator
            def create_full_plan():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(orchestrator.execute(state))
                finally:
                    loop.close()
            
            try:
                # Try to use existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, use executor
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, create_full_plan())
                        result_state = future.result(timeout=120)
                else:
                    result_state = loop.run_until_complete(create_full_plan())
            except RuntimeError:
                result_state = asyncio.run(create_full_plan())
            
            # Format response
            response_data = {
                'status': 'success',
                'plan': {
                    'transport': result_state.get('transport', {}),
                    'transport_breakdown': result_state.get('transport_breakdown'),
                    'flight': result_state.get('flight'),
                    'hotels': result_state.get('hotels', []),
                    'selected_hotel': result_state.get('selected_hotel'),
                    'activities': result_state.get('activities', []),
                    'restaurants': result_state.get('restaurants', []),
                    'budget': result_state.get('budget', {}),
                    'itinerary': result_state.get('itinerary', {}),
                    'itinerary_json': result_state.get('itinerary_json', {}),  # Thêm JSON data
                    'itinerary_description': result_state.get('itinerary_description', '')  # Thêm mô tả
                },
                'costs': {
                    'transport': result_state.get('transport_cost', 0) or result_state.get('budget', {}).get('breakdown', {}).get('transport', 0),
                    'accommodation': result_state.get('accommodation_cost', 0) or result_state.get('budget', {}).get('breakdown', {}).get('accommodation', 0),
                    'activities': result_state.get('activities_cost', 0) or result_state.get('budget', {}).get('breakdown', {}).get('activities', 0),
                    'dining': result_state.get('dining_cost', 0) or result_state.get('budget', {}).get('breakdown', {}).get('dining', 0),
                    'total': result_state.get('budget', {}).get('total_vnd', 0)
                },
                'timestamp': timezone.now()
            }
            
            # Cache result for 3 hours (itinerary generation is expensive, but user might want fresh data)
            cache_set(cache_key, response_data, ttl=10800)

            # Luồng 4 bước là một entrypoint riêng nên cũng cần ghi analytics riêng.
            ghi_nhan_yeu_cau_lo_trinh_async(
                user_id=request.user.pk if request.user.is_authenticated else None,
                loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.BUOC_4,
                trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                diem_di=origin,
                diem_den=destination,
                so_ngay_di=days,
                so_nguoi=travelers,
                ngan_sach_du_kien=validated_data.get('budget') or response_data.get('costs', {}).get('total'),
                ngay_khoi_hanh_du_kien=start_date,
                du_lieu_phan_hoi={
                    'transport': result_state.get('transport', {}),
                    'transport_breakdown': result_state.get('transport_breakdown'),
                    'budget': result_state.get('budget', {}),
                    'costs': response_data.get('costs', {}),
                    'selected_hotel': result_state.get('selected_hotel'),
                    'activities_count': len(result_state.get('activities', [])),
                    'restaurants_count': len(result_state.get('restaurants', [])),
                    'travel_style': travel_style,
                    'interests': interests,
                    'from_step4': True,
                },
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            try:
                request_data = request.data if hasattr(request, 'data') and isinstance(request.data, dict) else {}
                ghi_nhan_yeu_cau_lo_trinh_async(
                    user_id=request.user.pk if request.user.is_authenticated else None,
                    loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.BUOC_4,
                    trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THAT_BAI,
                    diem_di=locals().get('origin') or request_data.get('origin', ''),
                    diem_den=locals().get('destination') or request_data.get('destination', ''),
                    so_ngay_di=locals().get('days') or request_data.get('days'),
                    so_nguoi=locals().get('travelers') or request_data.get('travelers'),
                    ngan_sach_du_kien=request_data.get('budget'),
                    ngay_khoi_hanh_du_kien=locals().get('start_date') or request_data.get('start_date'),
                    du_lieu_phan_hoi={
                        'error_message': sanitize_sensitive_string(str(e)),
                        'error_type': e.__class__.__name__,
                        'travel_style': locals().get('travel_style') or request_data.get('travel_style', 'standard'),
                        'interests': locals().get('interests') or request_data.get('interests', []),
                        'from_step4': True,
                    },
                )
            except Exception:
                logger.exception("Không thể ghi analytics lỗi cho step4 request")
            logger.error(f"Error in Step 4: {e}", exc_info=True)
            return Response({
                'error': sanitize_sensitive_string(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Step4SaveItineraryView(APIView):
    """
    Save itinerary from Step 4 to database
    POST /api/v1/travel-plans/step4/save/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Save itinerary to database"""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            request_data = request.data if isinstance(request.data, dict) else {}
            plan = request_data.get('plan', {}) if isinstance(request_data.get('plan'), dict) else {}
            canonical_plan = plan.get('itinerary_json') if isinstance(plan.get('itinerary_json'), dict) else None
            if canonical_plan is None and isinstance(plan, dict) and 'trip_overview' in plan:
                canonical_plan = plan

            if not isinstance(canonical_plan, dict):
                return Response({
                    'error': 'Payload plan không đúng định dạng structured output.'
                }, status=status.HTTP_400_BAD_REQUEST)

            delegated_payload = dict(request_data)
            delegated_payload['plan'] = canonical_plan
            save_result = _save_structured_travel_plan_for_user(
                user=request.user,
                request_data=delegated_payload,
            )

            return Response({
                'status': save_result.get('status', 'success'),
                'message': save_result.get('message', 'Đã lưu lịch trình thành công'),
                'itinerary_id': save_result.get('maLichTrinh'),
                'itinerary': {
                    'id': save_result.get('maLichTrinh'),
                    'destination': request_data.get('destination'),
                    'start_date': request_data.get('start_date'),
                    'days': request_data.get('days')
                },
                'canonical_gateway': 'SaveTravelPlanView'
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            return Response({
                'error': 'Dữ liệu lịch trình đang được cập nhật đồng thời. Vui lòng thử lại.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error saving itinerary: {e}", exc_info=True)
            return Response({
                'error': sanitize_sensitive_string(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
