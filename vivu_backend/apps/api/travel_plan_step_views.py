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
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
import logging
import asyncio

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
        "origin": {...},
        "destination": {...},
        "distance_km": 1508.8,
        "estimated_duration": "18h 42m",
        "recommended_transport": "flight"
    }
    """
    permission_classes = [AllowAny]
    
    def _normalize_location_name(self, location: str) -> str:
        """
        Normalize location name from autocomplete format.
        
        Examples:
        - "Hải Dương (thuộc Thành phố Hải Phòng)" -> "Thành phố Hải Phòng"
        - "Bà Rịa - Vũng Tàu (thuộc Thành phố Hồ Chí Minh)" -> "Thành phố Hồ Chí Minh"
        - "Thành phố Hà Nội" -> "Thành phố Hà Nội" (unchanged)
        """
        if not location:
            return location
        
        # Check if it has "(thuộc...)" format
        import re
        match = re.search(r'\(thuộc\s+(.+?)\)', location)
        if match:
            # Extract the main province/city name
            main_location = match.group(1).strip()
            logger.info(f"Normalized location: '{location}' -> '{main_location}'")
            return main_location
        
        return location
    
    def post(self, request):
        try:
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            
            if not origin or not destination:
                raise ValidationError({
                    'error': 'Missing origin or destination'
                })
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=20, window=60):
                return Response({
                    'error': 'Rate limit exceeded. Maximum 20 requests per minute.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Normalize location names (handle autocomplete format with "(thuộc...)")
            origin_normalized = self._normalize_location_name(origin)
            destination_normalized = self._normalize_location_name(destination)
            
            # Check cache for Step 1 result
            cache_key = generate_cache_key('travel_step1', origin_normalized, destination_normalized)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for Step 1: {origin_normalized} -> {destination_normalized}")
                return Response(cached_result, status=status.HTTP_200_OK)
            
            # Sử dụng GeoTools (có fallback VietMap → OpenRouteService) và TransportTools
            from tools.geo_tools import get_geo_tools
            from tools.transport_tools import get_transport_tools
            
            geo_tools = get_geo_tools()
            transport_tools = get_transport_tools()
            
            # Geocode origin và destination (ưu tiên VietMap, fallback OpenRouteService)
            logger.info(f"Geocoding origin: {origin} (normalized: {origin_normalized})")
            origin_coords = geo_tools.geocode(origin_normalized, use_vietmap=True)
            
            logger.info(f"Geocoding destination: {destination} (normalized: {destination_normalized})")
            dest_coords = geo_tools.geocode(destination_normalized, use_vietmap=True)
            
            if not origin_coords:
                logger.warning(f"Cannot geocode origin: {origin} (normalized: {origin_normalized})")
                # Try with original name if normalized failed
                if origin_normalized != origin:
                    logger.info(f"Retrying geocode with original name: {origin}")
                    origin_coords = geo_tools.geocode(origin, use_vietmap=True)
                
                if not origin_coords:
                    return Response({
                        'error': f'Không thể tìm thấy địa điểm xuất phát: "{origin}". Vui lòng kiểm tra lại tên địa điểm.',
                        'origin': origin,
                        'suggestions': [
                            'Sử dụng tên tỉnh/thành phố đầy đủ (ví dụ: "Thành phố Hồ Chí Minh", "Thành phố Hà Nội")',
                            'Hoặc sử dụng autocomplete để chọn từ danh sách gợi ý',
                            'Kiểm tra chính tả và dấu tiếng Việt'
                        ]
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if not dest_coords:
                logger.warning(f"Cannot geocode destination: {destination} (normalized: {destination_normalized})")
                # Try with original name if normalized failed
                if destination_normalized != destination:
                    logger.info(f"Retrying geocode with original name: {destination}")
                    dest_coords = geo_tools.geocode(destination, use_vietmap=True)
                
                if not dest_coords:
                    return Response({
                        'error': f'Không thể tìm thấy địa điểm đến: "{destination}". Vui lòng kiểm tra lại tên địa điểm.',
                        'destination': destination,
                        'suggestions': [
                            'Sử dụng tên tỉnh/thành phố đầy đủ (ví dụ: "Thành phố Hồ Chí Minh", "Thành phố Hà Nội")',
                            'Hoặc sử dụng autocomplete để chọn từ danh sách gợi ý',
                            'Kiểm tra chính tả và dấu tiếng Việt'
                        ]
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Tính khoảng cách và thời gian (ưu tiên VietMap, fallback OpenRouteService)
            # Use normalized names for routing
            logger.info(f"Calculating route: {origin_normalized} -> {destination_normalized}")
            route_info = geo_tools.calculate_distance_time(
                origin_normalized, destination_normalized, profile='driving-car', use_vietmap=True
            )
            
            if not route_info:
                logger.warning(f"Cannot calculate route: {origin} -> {destination}")
                # Fallback: Tính khoảng cách đơn giản từ tọa độ (Haversine)
                from math import radians, sin, cos, sqrt, atan2
                
                # Validate coordinates trước khi dùng
                if not origin_coords or not origin_coords.get('lat') or not origin_coords.get('lon'):
                    logger.error(f"Invalid origin_coords: {origin_coords}")
                    return Response({
                        'error': f'Không thể lấy tọa độ cho điểm xuất phát: "{origin}"',
                        'origin': origin
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not dest_coords or not dest_coords.get('lat') or not dest_coords.get('lon'):
                    logger.error(f"Invalid dest_coords: {dest_coords}")
                    return Response({
                        'error': f'Không thể lấy tọa độ cho điểm đến: "{destination}"',
                        'destination': destination
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                lat1, lon1 = radians(origin_coords['lat']), radians(origin_coords['lon'])
                lat2, lon2 = radians(dest_coords['lat']), radians(dest_coords['lon'])
                
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance_km = 6371 * c  # Earth radius in km
                
                # Ước tính thời gian (50km/h trung bình cho đường bộ)
                duration_minutes = (distance_km / 50) * 60
                
                route_info = {
                    'distance_km': round(distance_km, 1),
                    'duration_minutes': round(duration_minutes, 1)
                }
                
                logger.info(f"Using Haversine fallback: {route_info['distance_km']} km, {route_info['duration_minutes']} min")
            
            # Đề xuất phương tiện
            suggestion = transport_tools.suggest_transport(
                origin, destination, route_info['distance_km']
            )
            
            # Format response
            hours = int(route_info['duration_minutes'] // 60)
            minutes = int(route_info['duration_minutes'] % 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            # Return original names from user input, but use normalized for display if different
            origin_display = origin_normalized if origin_normalized != origin else origin
            destination_display = destination_normalized if destination_normalized != destination else destination
            
            response_data = {
                'status': 'success',
                'origin': {
                    'name': origin_display,  # Show normalized name (the actual location)
                    'original_name': origin if origin != origin_normalized else None,  # Keep original for reference
                    'coordinates': {
                        'lat': origin_coords['lat'],
                        'lon': origin_coords['lon']
                    },
                    'formatted_address': origin_coords.get('formatted_address', origin)
                },
                'destination': {
                    'name': destination_display,  # Show normalized name (the actual location)
                    'original_name': destination if destination != destination_normalized else None,  # Keep original for reference
                    'coordinates': {
                        'lat': dest_coords['lat'],
                        'lon': dest_coords['lon']
                    },
                    'formatted_address': dest_coords.get('formatted_address', destination_display)
                },
                'distance_km': round(route_info['distance_km'], 1),
                'estimated_duration': duration_str,
                'estimated_duration_minutes': round(route_info['duration_minutes'], 1),
                'recommended_transport': suggestion.get('method', 'car'),
                'transport_icon': self._get_transport_icon(suggestion.get('method', 'car')),
                'timestamp': timezone.now()
            }
            
            # Cache result for 24 hours (geocoding and routes don't change often)
            cache_set(cache_key, response_data, ttl=86400)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in Step 1: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_transport_icon(self, method: str) -> str:
        """Get icon for transport method"""
        icons = {
            'flight': '✈️',
            'train': '🚂',
            'bus': '🚌',
            'car': '🚗',
            'motorcycle': '🏍️'
        }
        return icons.get(method, '🚗')


class Step2TravelInfoView(APIView):
    """
    Step 2: Thông tin du lịch (khoảng cách, phương tiện, thời tiết)
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
        "transport_options": [...],
        "recommended_transport": "flight",
        "weather_forecast": {...},
        "recommended_days": 3
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 2))
            
            if not all([origin, destination, start_date, days]):
                raise ValidationError({
                    'error': 'Missing required parameters: origin, destination, start_date, days'
                })
            
            if days < 1:
                raise ValidationError({
                    'error': 'Số ngày phải lớn hơn 0',
                    'days': days
                })
            
            if days > 14:
                raise ValidationError({
                    'error': 'Số ngày không được vượt quá 14 ngày',
                    'days': days,
                    'max_days': 14
                })
            
            if travelers < 1:
                raise ValidationError({
                    'error': 'Số người phải lớn hơn 0',
                    'travelers': travelers
                })
            
            if travelers > 20:
                raise ValidationError({
                    'error': 'Vui lòng nhập số người dưới 20 để đảm bảo chất lượng chuyến đi',
                    'travelers': travelers,
                    'max_travelers': 20
                })
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=20, window=60):
                return Response({
                    'error': 'Rate limit exceeded.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Check cache for Step 2 result (cache based on params, not date-sensitive)
            cache_key = generate_cache_key('travel_step2', origin, destination, days, travelers)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for Step 2: {origin} -> {destination}, {days}d, {travelers}p")
                # Update timestamp
                cached_result['timestamp'] = timezone.now()
                return Response(cached_result, status=status.HTTP_200_OK)
            
            # Sử dụng Transport Agent để lấy thông tin vận chuyển
            from agents.travel_agents.transport_agent import TransportAgent
            
            state = {
                'origin': origin,
                'destination': destination,
                'start_date': start_date,
                'days': days,
                'travelers': travelers
            }
            
            transport_agent = TransportAgent()
            
            async def get_transport_info():
                return await transport_agent.execute(state)
            
            # Run async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, get_transport_info())
                        result_state = future.result(timeout=30)
                else:
                    result_state = loop.run_until_complete(get_transport_info())
            except RuntimeError:
                result_state = asyncio.run(get_transport_info())
            
            transport = result_state.get('transport', {})
            
            # Lấy thời tiết (nếu có API key)
            weather_forecast = self._get_weather_forecast(destination, start_date)
            
            # Đề xuất số ngày hợp lý (dựa trên khoảng cách)
            recommended_days = self._suggest_days(transport.get('distance_km', 0))
            
            response_data = {
                'status': 'success',
                'transport': {
                    'distance_km': transport.get('distance_km', 0),
                    'duration_minutes': transport.get('duration_minutes', 0),
                    'suggested_method': transport.get('suggested_method', 'car'),
                    'estimated_cost_vnd': transport.get('estimated_cost_vnd', 0),
                    'options': self._get_transport_options(transport.get('distance_km', 0))
                },
                'recommended_transport': transport.get('suggested_method', 'car'),
                'recommended_days': recommended_days,
                'weather_forecast': weather_forecast,
                'timestamp': timezone.now()
            }
            
            # Cache result for 12 hours (transport options don't change often)
            cache_set(cache_key, response_data, ttl=43200)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in Step 2: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_transport_options(self, distance_km: float) -> list:
        """Get available transport options based on distance"""
        options = []
        
        if distance_km > 500:
            options.append({
                'method': 'flight',
                'icon': '✈️',
                'name': 'Máy bay',
                'estimated_time': f'{int(distance_km / 700)}h',
                'estimated_cost_vnd': int(distance_km * 1500)
            })
        
        if distance_km > 200:
            options.append({
                'method': 'train',
                'icon': '🚂',
                'name': 'Tàu hỏa',
                'estimated_time': f'{int(distance_km / 60)}h',
                'estimated_cost_vnd': int(distance_km * 800)
            })
        
        options.append({
            'method': 'bus',
            'icon': '🚌',
            'name': 'Xe khách',
            'estimated_time': f'{int(distance_km / 50)}h',
            'estimated_cost_vnd': int(distance_km * 500)
        })
        
        return options
    
    def _get_weather_forecast(self, destination: str, start_date: str) -> dict:
        """Get weather forecast (placeholder - có thể tích hợp OpenWeather API sau)"""
        # TODO: Tích hợp OpenWeather API nếu có API key
        return {
            'status': 'not_available',
            'message': 'Dự báo thời tiết sẽ được tích hợp trong tương lai'
        }
    
    def _suggest_days(self, distance_km: float) -> int:
        """Suggest number of days based on distance"""
        if distance_km < 200:
            return 2
        elif distance_km < 500:
            return 3
        elif distance_km < 1000:
            return 4
        else:
            return 5


class Step3BudgetSuggestionView(APIView):
    """
    Step 3: Gợi ý ngân sách & chọn khách sạn
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
        "budget": {...},
        "hotels": [...]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 2))
            travel_style = request.data.get('travel_style', 'standard')
            rooms = int(request.data.get('rooms', 1))
            
            if not all([origin, destination, start_date, days]):
                raise ValidationError({
                    'error': 'Missing required parameters'
                })
            
            # Validate days (1-14)
            if days < 1:
                raise ValidationError({
                    'error': 'Số ngày phải lớn hơn 0',
                    'days': days
                })
            
            if days > 14:
                raise ValidationError({
                    'error': 'Số ngày không được vượt quá 14 ngày',
                    'days': days,
                    'max_days': 14
                })
            
            # Validate travelers (1-20)
            if travelers < 1:
                raise ValidationError({
                    'error': 'Số người phải lớn hơn 0',
                    'travelers': travelers
                })
            
            if travelers > 20:
                raise ValidationError({
                    'error': 'Vui lòng nhập số người dưới 20 để đảm bảo chất lượng chuyến đi',
                    'travelers': travelers,
                    'max_travelers': 20
                })
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=20, window=60):
                return Response({
                    'error': 'Rate limit exceeded.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Check cache for Step 3 result (cache hotel searches and budget)
            cache_key = generate_cache_key('travel_step3', destination, days, travelers, travel_style, rooms)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for Step 3: {destination}, {days}d, {travelers}p, {travel_style}")
                cached_result['timestamp'] = timezone.now()
                return Response(cached_result, status=status.HTTP_200_OK)
            
            # Sử dụng Transport, Budget và Accommodation agents
            from agents.travel_agents.transport_agent import TransportAgent
            from agents.travel_agents.budget_agent import BudgetAgent
            from agents.travel_agents.accommodation_agent import AccommodationAgent
            
            state = {
                'origin': origin,
                'destination': destination,
                'start_date': start_date,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'rooms': rooms
            }
            
            async def get_step3_data():
                # Transport
                transport_agent = TransportAgent()
                state_result = await transport_agent.execute(state)
                
                # Flight Agent - Nếu phương tiện là máy bay, tính chi phí đầy đủ
                if state_result.get('transport', {}).get('suggested_method') == 'flight':
                    from agents.travel_agents.flight_agent import FlightAgent
                    from tools.airport_utils import get_nearest_airport, calculate_airport_transport_cost
                    from tools.geo_tools import get_geo_tools
                    
                    origin = state_result.get('origin')
                    destination = state_result.get('destination')
                    travelers = state_result.get('travelers', 1)
                    
                    # Xác định sân bay gần nhất
                    origin_airport_info = get_nearest_airport(origin)
                    dest_airport_info = get_nearest_airport(destination)
                    
                    if origin_airport_info and dest_airport_info:
                        geo_tools = get_geo_tools()
                        
                        # 1. Tính chi phí từ origin → sân bay đi
                        origin_to_airport_route = geo_tools.calculate_distance_time(
                            origin, f"{origin_airport_info[1]}, {origin_airport_info[2]}"
                        )
                        origin_to_airport_cost = 0
                        method_to_airport = 'taxi'
                        if origin_to_airport_route:
                            origin_to_airport_dist = origin_to_airport_route['distance_km']
                            method_to_airport = 'bus' if origin_to_airport_dist > 50 else 'taxi'
                            origin_to_airport_info_cost = calculate_airport_transport_cost(
                                origin, origin_airport_info[1], origin_to_airport_dist, method_to_airport
                            )
                            origin_to_airport_cost = origin_to_airport_info_cost['cost_vnd'] * travelers
                        
                        # 2. Tính giá vé máy bay
                        flight_agent = FlightAgent()
                        flight_state = {
                            'origin': origin_airport_info[0],
                            'destination': dest_airport_info[0],
                            'departure_date': start_date,
                            'passengers': travelers
                        }
                        flight_state = await flight_agent.execute(flight_state)
                        
                        flight_price = 0
                        if flight_state.get('flight'):
                            flight_price = (
                                flight_state['flight'].get('price_vnd', 0) or
                                flight_state['flight'].get('price', 0) or
                                flight_state['flight'].get('total_price_vnd', 0) or
                                0
                            )
                        
                        # Ước tính nếu không có giá từ API
                        if flight_price == 0:
                            distance_km = state_result.get('transport', {}).get('distance_km', 0)
                            if distance_km > 0:
                                estimated_price_per_person = min(max(distance_km * 2000, 1_500_000), 8_000_000)
                                flight_price = estimated_price_per_person * travelers
                            else:
                                flight_price = 3_000_000 * travelers
                        
                        # 3. Tính chi phí từ sân bay đến → destination
                        airport_to_dest_route = geo_tools.calculate_distance_time(
                            f"{dest_airport_info[1]}, {dest_airport_info[2]}", destination
                        )
                        airport_to_dest_cost = 0
                        method_from_airport = 'bus'
                        if airport_to_dest_route:
                            airport_to_dest_dist = airport_to_dest_route['distance_km']
                            if airport_to_dest_dist < 30:
                                method_from_airport = 'taxi'
                                airport_to_dest_info_cost = calculate_airport_transport_cost(
                                    dest_airport_info[1], destination, airport_to_dest_dist, method_from_airport
                                )
                                airport_to_dest_cost = airport_to_dest_info_cost['cost_vnd'] * travelers
                            elif airport_to_dest_dist < 200:
                                method_from_airport = 'bus'
                                airport_to_dest_info_cost = calculate_airport_transport_cost(
                                    dest_airport_info[1], destination, airport_to_dest_dist, method_from_airport
                                )
                                airport_to_dest_cost = airport_to_dest_info_cost['cost_vnd'] * travelers
                            else:
                                # Xa: xe buýt đường dài
                                method_from_airport = 'bus_long_distance'
                                # Xe buýt đường dài: ~3,000 VNĐ/km (rẻ hơn taxi)
                                airport_to_dest_cost = airport_to_dest_dist * 3000 * travelers
                        
                        # Tổng chi phí vận chuyển
                        total_transport_cost = origin_to_airport_cost + flight_price + airport_to_dest_cost
                        state_result['transport_cost'] = total_transport_cost
                        state_result['transport_breakdown'] = {
                            'origin_to_airport': {
                                'cost_vnd': origin_to_airport_cost,
                                'method': method_to_airport,
                                'distance_km': origin_to_airport_route['distance_km'] if origin_to_airport_route else 0,
                                'airport': origin_airport_info[1]
                            },
                            'flight': {
                                'cost_vnd': flight_price,
                                'origin_airport': origin_airport_info[1],
                                'dest_airport': dest_airport_info[1]
                            },
                            'airport_to_dest': {
                                'cost_vnd': airport_to_dest_cost,
                                'method': method_from_airport,
                                'distance_km': airport_to_dest_route['distance_km'] if airport_to_dest_route else 0,
                                'airport': dest_airport_info[1]
                            },
                            'total_vnd': total_transport_cost
                        }
                        
                        # Restore origin/destination
                        state_result['origin'] = origin
                        state_result['destination'] = destination
                
                # Accommodation
                accommodation_agent = AccommodationAgent()
                state_result['check_in'] = start_date
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = start + timedelta(days=days)
                state_result['check_out'] = end.strftime('%Y-%m-%d')
                state_result = await accommodation_agent.execute(state_result)
                
                # Budget
                budget_agent = BudgetAgent()
                state_result = await budget_agent.execute(state_result)
                
                return state_result
            
            # Run async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, get_step3_data())
                        result_state = future.result(timeout=60)
                else:
                    result_state = loop.run_until_complete(get_step3_data())
            except RuntimeError:
                result_state = asyncio.run(get_step3_data())
            
            response_data = {
                'status': 'success',
                'budget': result_state.get('budget', {}),
                'hotels': result_state.get('hotels', [])[:10],  # Limit to 10
                'transport': result_state.get('transport', {}),
                'timestamp': timezone.now()
            }
            
            # Cache result for 6 hours (hotel prices change but not too frequently)
            cache_set(cache_key, response_data, ttl=21600)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
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
        try:
            # Validate request
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            start_date = request.data.get('start_date')
            days = int(request.data.get('days', 1))
            travelers = int(request.data.get('travelers', 2))
            travel_style = request.data.get('travel_style', 'standard')
            rooms = int(request.data.get('rooms', 1))
            selected_hotel = request.data.get('selected_hotel')
            interests = request.data.get('interests', [])
            
            if not all([origin, destination, start_date, days]):
                raise ValidationError({
                    'error': 'Missing required parameters'
                })
            
            # Validate days (1-14)
            if days < 1:
                raise ValidationError({
                    'error': 'Số ngày phải lớn hơn 0',
                    'days': days
                })
            
            if days > 14:
                raise ValidationError({
                    'error': 'Số ngày không được vượt quá 14 ngày',
                    'days': days,
                    'max_days': 14
                })
            
            # Validate travelers (1-20)
            if travelers < 1:
                raise ValidationError({
                    'error': 'Số người phải lớn hơn 0',
                    'travelers': travelers
                })
            
            if travelers > 20:
                raise ValidationError({
                    'error': 'Vui lòng nhập số người dưới 20 để đảm bảo chất lượng chuyến đi',
                    'travelers': travelers,
                    'max_travelers': 20
                })
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=10, window=60):
                return Response({
                    'error': 'Rate limit exceeded.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Check cache for Step 4 result (cache full itinerary)
            # Note: Step 4 is expensive, cache for shorter time but still useful
            cache_key = generate_cache_key('travel_step4', origin, destination, start_date, days, travelers, travel_style, rooms, str(interests))
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for Step 4: {destination}, {days}d, {travelers}p")
                cached_result['timestamp'] = timezone.now()
                return Response(cached_result, status=status.HTTP_201_CREATED)
            
            # Sử dụng Orchestrator Agent để tạo plan đầy đủ
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            
            state = {
                'origin': origin,
                'destination': destination,
                'start_date': start_date,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'rooms': rooms,
                'interests': interests
            }
            
            if selected_hotel:
                state['selected_hotel'] = selected_hotel
            
            orchestrator = OrchestratorAgent()
            
            async def create_full_plan():
                return await orchestrator.execute(state)
            
            # Run async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
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
                    'itinerary': result_state.get('itinerary', {})
                },
                'costs': {
                    'transport': result_state.get('transport_cost', 0),
                    'accommodation': result_state.get('accommodation_cost', 0),
                    'activities': result_state.get('activities_cost', 0),
                    'dining': result_state.get('dining_cost', 0),
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

