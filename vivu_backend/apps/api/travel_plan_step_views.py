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
import logging
import asyncio

# Add backend directory to path for agents, tools, utils, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import caching utilities
from utils.cache import cache_get, cache_set, generate_cache_key

logger = logging.getLogger(__name__)


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
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 1))
            
            if not origin or not destination or not start_date:
                return Response({
                    'error': 'Vui lòng điền đầy đủ thông tin'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate days
            if days < 1 or days > 14:
                return Response({
                    'error': 'Số ngày phải từ 1 đến 14'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate travelers
            if travelers < 1 or travelers > 20:
                return Response({
                    'error': 'Số người phải từ 1 đến 20'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 1))
            travel_style = request.data.get('travel_style', 'standard')
            rooms = int(request.data.get('rooms', 1))
            
            if not origin or not destination or not start_date:
                return Response({
                    'error': 'Vui lòng điền đầy đủ thông tin'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get selected transport from request (if user selected in Step 2)
            selected_transport = request.data.get('selected_transport')
            
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
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 1))
            travel_style = request.data.get('travel_style', 'standard')
            rooms = int(request.data.get('rooms', 1))
            selected_hotel = request.data.get('selected_hotel')
            interests = request.data.get('interests', [])
            
            if not origin or not destination or not start_date:
                return Response({
                    'error': 'Vui lòng điền đầy đủ thông tin'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in Step 4: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Step4SaveItineraryView(APIView):
    """
    Save itinerary from Step 4 to database
    POST /api/v1/travel-plans/step4/save/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Save itinerary to database"""
        try:
            plan = request.data.get('plan', {})
            costs = request.data.get('costs', {})
            itinerary_json = plan.get('itinerary_json', {})
            itinerary_description = plan.get('itinerary_description', '')
            
            # Get basic info
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = request.data.get('days', 1)
            travelers = request.data.get('travelers', 2)
            travel_style = request.data.get('travel_style', 'standard')
            
            if not destination or not start_date:
                return Response({
                    'error': 'Missing required fields: destination, start_date'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse dates
            from datetime import datetime, timedelta
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = start + timedelta(days=days - 1)
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Expected YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find TinhThanh from destination name
            from apps.places.models import TinhThanh
            from agents.travel_agents.activities_agent import _normalize_location_name, _tokenize_normalized_name
            
            tinh_thanh = None
            dest_norm = _normalize_location_name(destination)
            if dest_norm:
                dest_tokens = _tokenize_normalized_name(dest_norm)
                if dest_tokens:
                    all_tinh_thanhs = list(TinhThanh.objects.all())
                    best_tinh_thanh = None
                    best_score = 0.0
                    
                    for tt in all_tinh_thanhs:
                        tt_norm = _normalize_location_name(tt.tenTinhThanh)
                        tt_tokens = _tokenize_normalized_name(tt_norm)
                        if not tt_tokens:
                            continue
                        common = dest_tokens & tt_tokens
                        if not common:
                            continue
                        union = dest_tokens | tt_tokens
                        if not union:
                            continue
                        score = len(common) / len(union)
                        if score > best_score:
                            best_score = score
                            best_tinh_thanh = tt
                    
                    if best_tinh_thanh and best_score >= 0.4:
                        tinh_thanh = best_tinh_thanh
            
            # Create title
            style_labels = {
                'budget': 'Tiết kiệm',
                'standard': 'Tiêu chuẩn',
                'luxury': 'Cao cấp',
                'eco': 'Sinh thái',
                'romantic': 'Lãng mạn',
                'adventure': 'Phiêu lưu',
                'cultural': 'Văn hóa',
                'gastronomy': 'Ẩm thực',
                'wellness': 'Sức khỏe',
                'family': 'Gia đình'
            }
            style_label = style_labels.get(travel_style, 'Tiêu chuẩn')
            title = f"Lịch trình {days} ngày đến {destination} - {style_label}"
            
            # Create description from LLM-generated text or fallback
            description = itinerary_description or plan.get('itinerary', {}).get('summary', '')
            
            # Prepare chiTiet JSON (full state data)
            chi_tiet_data = {
                'itinerary_json': itinerary_json,
                'itinerary_description': itinerary_description,
                'plan': plan,
                'costs': costs,
                'origin': origin,
                'destination': destination,
                'travel_style': travel_style
            }
            
            # Save to database
            from apps.itineraries.models import LichTrinh
            import json
            
            lich_trinh = LichTrinh.objects.create(
                maNguoiDung=request.user,
                maTinhThanh=tinh_thanh,
                tieuDe=title,
                moTa=description[:1000] if description else '',  # Limit description length
                ngayBatDau=start.date(),
                ngayKetThuc=end.date(),
                soNgay=days,
                soNguoi=travelers,
                nganSach=None,  # Can be added later
                chiPhiUocTinh=costs.get('total', 0),
                trangThai='published',
                laCongKhai=False,
                chiTiet=json.dumps(chi_tiet_data, ensure_ascii=False)
            )
            
            # Save itinerary places (LichTrinhDiaDiem) if we have itinerary_json
            if itinerary_json and 'DIADIEM' in itinerary_json and 'LICHTRINH_DIADIEM' in itinerary_json:
                from apps.places.models import DiaDiem
                from apps.itineraries.models import LichTrinhDiaDiem
                
                diadiem_map = {}  # Map place name to DiaDiem object
                for diadiem_data in itinerary_json.get('DIADIEM', []):
                    ten_dia_diem = diadiem_data.get('tenDiaDiem', '')
                    if ten_dia_diem:
                        # Try to find in database
                        dia_diem = DiaDiem.objects.filter(
                            tenDiaDiem__icontains=ten_dia_diem,
                            trangThai='active'
                        ).first()
                        if dia_diem:
                            diadiem_map[ten_dia_diem] = dia_diem
                
                # Create LichTrinhDiaDiem entries
                for ltdd_data in itinerary_json.get('LICHTRINH_DIADIEM', []):
                    ten_dia_diem = ltdd_data.get('tenDiaDiem', '')
                    if ten_dia_diem in diadiem_map:
                        try:
                            ngay_tham_quan_str = ltdd_data.get('ngayThamQuan', '')
                            if ngay_tham_quan_str:
                                # Parse date from string (format: YYYY-MM-DD)
                                ngay_tham_quan = datetime.strptime(ngay_tham_quan_str, '%Y-%m-%d').date()
                            else:
                                # Fallback to start_date + ngayThu - 1
                                ngay_thu = ltdd_data.get('ngayThu', 1)
                                ngay_tham_quan = start.date() + timedelta(days=ngay_thu - 1)
                            
                            LichTrinhDiaDiem.objects.create(
                                maLichTrinh=lich_trinh,
                                maDiaDiem=diadiem_map[ten_dia_diem],
                                ngayThamQuan=ngay_tham_quan,
                                thoiGianThamQuan=ltdd_data.get('thoiGianThamQuan', ''),
                                thuTu=ltdd_data.get('thuTu', 1),
                                ghiChu=ltdd_data.get('ghiChu', ''),
                                chiPhiUocTinh=ltdd_data.get('chiPhiUocTinh', 0)
                            )
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Error creating LichTrinhDiaDiem: {e}")
                            continue
            
            return Response({
                'status': 'success',
                'message': 'Lịch trình đã được lưu thành công',
                'itinerary_id': lich_trinh.maLichTrinh,
                'itinerary': {
                    'id': lich_trinh.maLichTrinh,
                    'title': lich_trinh.tieuDe,
                    'destination': destination,
                    'start_date': start_date,
                    'days': days
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error saving itinerary: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
