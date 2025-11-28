"""
Geographic Tools - Công cụ địa lý
==================================
- Geocoding (chuyển đổi tên địa điểm → tọa độ)
- Tính khoảng cách và thời gian di chuyển
- Tìm địa điểm trong bán kính

Hỗ trợ cả OpenRouteService và VietMap API (ưu tiên VietMap cho địa chỉ Việt Nam)
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
import requests
import os
from functools import lru_cache

# Import caching utilities
try:
    from utils.cache import cache_get, cache_set, generate_cache_key, cached
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache utilities not available")

logger = logging.getLogger(__name__)


def normalize_location_name(location: str) -> List[str]:
    """
    Normalize location name để xử lý các biến thể tên địa điểm
    Trả về danh sách các biến thể để thử geocode
    
    Args:
        location: Tên địa điểm gốc
        
    Returns:
        List các biến thể tên để thử (theo thứ tự ưu tiên)
    """
    location = location.strip()
    variants = [location]  # Luôn thử tên gốc trước
    
    location_lower = location.lower()
    
    # Xử lý "Thành phố X" -> "X"
    if location_lower.startswith('thành phố '):
        # Tìm vị trí kết thúc của "thành phố " (có thể có khoảng trắng)
        prefix_len = len('thành phố ')
        city_name = location[prefix_len:].strip()
        if city_name:
            variants.append(city_name)
            # Thêm biến thể với "TP."
            if not city_name.lower().startswith('tp.'):
                variants.append(f"TP. {city_name}")
    
    # Xử lý "TP. X" hoặc "TP X" -> "X"
    if location_lower.startswith('tp.'):
        city_name = location[3:].strip()
        if city_name:
            variants.append(city_name)
            variants.append(f"Thành phố {city_name}")
    elif location_lower.startswith('tp '):
        city_name = location[3:].strip()
        if city_name:
            variants.append(city_name)
            variants.append(f"Thành phố {city_name}")
    
    # Xử lý "tỉnh X" -> "X"
    if location_lower.startswith('tỉnh '):
        prefix_len = len('tỉnh ')
        province_name = location[prefix_len:].strip()
        if province_name:
            variants.append(province_name)
    
    # Xử lý "Thừa Thiên Huế" -> "Huế"
    if 'thừa thiên' in location_lower and 'huế' in location_lower:
        variants.append('Huế')
        variants.append('Thành phố Huế')
    
    # Xử lý "Hồ Chí Minh" variants
    if 'hồ chí minh' in location_lower or 'ho chi minh' in location_lower:
        variants.extend(['TP. Hồ Chí Minh', 'Hồ Chí Minh', 'TP.HCM', 'Sài Gòn'])
    
    # Xử lý "Hà Nội" variants
    if 'hà nội' in location_lower or 'ha noi' in location_lower:
        variants.extend(['Hà Nội', 'Thành phố Hà Nội'])
    
    # Xử lý "Đà Nẵng" variants
    if 'đà nẵng' in location_lower or 'da nang' in location_lower:
        variants.extend(['Đà Nẵng', 'Thành phố Đà Nẵng'])
    
    # Xử lý "Cần Thơ" variants
    if 'cần thơ' in location_lower or 'can tho' in location_lower:
        variants.extend(['Cần Thơ', 'Thành phố Cần Thơ'])
    
    # Loại bỏ duplicates nhưng giữ thứ tự
    seen = set()
    unique_variants = []
    for variant in variants:
        variant_lower = variant.lower().strip()
        if variant_lower and variant_lower not in seen:
            seen.add(variant_lower)
            unique_variants.append(variant.strip())
    
    return unique_variants


class GeoTools:
    """Công cụ địa lý cho các agents - Hỗ trợ OpenRouteService và VietMap"""
    
    def __init__(self):
        # Try to get from Django settings first (if running in Django context)
        try:
            from django.conf import settings
            self.openroute_api_key = getattr(settings, 'OPENROUTE_API_KEY', '')
            self.vietmap_api_key = getattr(settings, 'VIETMAP_API_KEY', '')
        except (ImportError, AttributeError):
            # Fallback to environment variable
            self.openroute_api_key = os.getenv('OPENROUTE_API_KEY', '')
            self.vietmap_api_key = os.getenv('VIETMAP_API_KEY', '')
        
        self.base_url = "https://api.openrouteservice.org"
        
        # Try to initialize VietMap tools if available
        self.vietmap = None
        if self.vietmap_api_key:
            try:
                from tools.vietmap_tools import get_vietmap_tools
                self.vietmap = get_vietmap_tools()
                logger.info("VietMap API initialized (preferred for Vietnam addresses)")
            except Exception as e:
                logger.warning(f"VietMap tools not available: {e}")
        
    def geocode(self, location: str, country: str = "VN", use_vietmap: bool = True) -> Optional[Dict[str, Any]]:
        """
        Chuyển đổi tên địa điểm thành tọa độ
        
        Ưu tiên VietMap cho địa chỉ Việt Nam, fallback về OpenRouteService
        
        Args:
            location: Tên địa điểm (ví dụ: "Hà Nội", "TP. Hồ Chí Minh", "Mỹ Sơn")
            country: Mã quốc gia (mặc định: "VN")
            use_vietmap: Ưu tiên dùng VietMap nếu có (mặc định: True)
            
        Returns:
            Dict với 'lat', 'lon', 'formatted_address' hoặc None
        """
        # Check cache first
        if CACHE_AVAILABLE:
            cache_key = generate_cache_key('geocode', location, country, use_vietmap)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for geocode: {location}")
                return cached_result
        
        # Thử VietMap trước nếu có (ưu tiên cho địa chỉ Việt Nam)
        if use_vietmap and self.vietmap:
            # Thử với các biến thể tên địa điểm
            location_variants = normalize_location_name(location)
            for variant in location_variants:
                try:
                    result = self.vietmap.geocode(variant)
                    if result:
                        logger.debug(f"Geocoded via VietMap: {location} (tried variant: {variant})")
                        # Cache result cho cả tên gốc và variant
                        if CACHE_AVAILABLE:
                            cache_key = generate_cache_key('geocode', location, country, use_vietmap)
                            cache_set(cache_key, result, ttl=604800)  # 7 days
                            # Cache cho variant cũng
                            variant_key = generate_cache_key('geocode', variant, country, use_vietmap)
                            cache_set(variant_key, result, ttl=604800)
                        return result
                except Exception as e:
                    logger.debug(f"VietMap geocoding failed for variant '{variant}': {e}")
                    continue
            logger.debug(f"VietMap geocoding failed for all variants, trying OpenRouteService")
        
        # Fallback to OpenRouteService
        if not self.openroute_api_key:
            logger.warning("No geocoding API key available (OPENROUTE_API_KEY or VIETMAP_API_KEY)")
            return None
        
        # Thử với các biến thể tên địa điểm
        location_variants = normalize_location_name(location)
        for variant in location_variants:
            try:
                url = f"{self.base_url}/geocode/search"
                params = {
                    'api_key': self.openroute_api_key,
                    'text': variant,
                    'boundary.country': country,
                    'size': 1
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('features') and len(data['features']) > 0:
                    feature = data['features'][0]
                    geometry = feature.get('geometry', {})
                    properties = feature.get('properties', {})
                    
                    result = {
                        'lat': geometry.get('coordinates', [0, 0])[1],
                        'lon': geometry.get('coordinates', [0, 0])[0],
                        'formatted_address': properties.get('label', location),
                        'confidence': properties.get('confidence', 0.0)
                    }
                    
                    logger.debug(f"Geocoded via OpenRouteService: {location} (tried variant: {variant})")
                    
                    # Cache result for 7 days (geocoding rarely changes)
                    if CACHE_AVAILABLE:
                        cache_key = generate_cache_key('geocode', location, country, use_vietmap)
                        cache_set(cache_key, result, ttl=604800)
                        # Cache cho variant cũng
                        variant_key = generate_cache_key('geocode', variant, country, use_vietmap)
                        cache_set(variant_key, result, ttl=604800)
                    
                    return result
            except Exception as e:
                logger.debug(f"OpenRouteService geocoding failed for variant '{variant}': {e}")
                continue
        
        logger.error(f"Geocoding error for {location}: all variants failed")
        return None
    
    def calculate_distance_time(
        self, 
        origin: str, 
        destination: str,
        profile: str = "driving-car",
        use_vietmap: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Tính khoảng cách và thời gian di chuyển
        
        Ưu tiên VietMap cho routing trong Việt Nam, fallback về OpenRouteService
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            profile: Loại phương tiện (driving-car/car, cycling-regular/bike, foot-walking/foot)
            use_vietmap: Ưu tiên dùng VietMap nếu có (mặc định: True)
            
        Returns:
            Dict với 'distance_km', 'duration_minutes', 'route' hoặc None
        """
        # Normalize coordinates to ensure consistent cache keys
        # Remove spaces and normalize format: "lat,lon" -> "lat,lon"
        def normalize_coord(coord_str: str) -> str:
            """Normalize coordinate string for consistent caching"""
            if ',' in coord_str:
                # It's a coordinate pair
                parts = coord_str.split(',')
                if len(parts) == 2:
                    try:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                        # Round to 7 decimal places (about 1cm precision) for consistent caching
                        return f"{lat:.7f},{lon:.7f}"
                    except ValueError:
                        pass
            return coord_str.strip()
        
        normalized_origin = normalize_coord(origin)
        normalized_destination = normalize_coord(destination)
        
        # Check cache first with normalized coordinates
        if CACHE_AVAILABLE:
            cache_key = generate_cache_key('route', normalized_origin, normalized_destination, profile, use_vietmap)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for route: {normalized_origin} -> {normalized_destination}")
                return cached_result
        
        # Map profile names
        profile_map = {
            'driving-car': 'car',
            'cycling-regular': 'bike',
            'foot-walking': 'foot'
        }
        vietmap_profile = profile_map.get(profile, 'car')
        
        # Thử VietMap trước nếu có (sử dụng normalized coordinates)
        if use_vietmap and self.vietmap:
            try:
                logger.info(f"Calculating route: {normalized_origin} -> {normalized_destination} via VietMap")
                result = self.vietmap.calculate_distance_time(normalized_origin, normalized_destination, vietmap_profile)
                
                # CRITICAL FIX: Validate distance > 0 and reasonable before accepting result
                if result and result.get('distance_km', 0) > 0:
                    distance_km = result.get('distance_km', 0)
                    
                    # Validate: Check if distance is reasonable (not > 2000km for domestic routes)
                    # If distance > 2000km, likely geocoding error, try fallback
                    if distance_km > 2000:
                        logger.warning(f"VietMap returned suspiciously large distance ({distance_km} km) for {origin} -> {destination}, trying fallback")
                        # Don't return, continue to fallback
                    else:
                        logger.info(f"VietMap routing successful: {distance_km} km, {result.get('duration_minutes', 0)} min")
                        # Cache result with normalized coordinates - TTL 7 days (routes don't change often)
                        if CACHE_AVAILABLE:
                            cache_key = generate_cache_key('route', normalized_origin, normalized_destination, profile, use_vietmap)
                            cache_set(cache_key, result, ttl=604800)  # 7 days (routes rarely change)
                        return result
                else:
                    logger.warning(f"VietMap returned invalid distance (0 or None), trying OpenRouteService fallback")
            except Exception as e:
                logger.warning(f"VietMap routing failed: {e}, trying OpenRouteService fallback")
        
        # Geocode cả 2 điểm TRƯỚC KHI tính routing để validate (sử dụng normalized coordinates nếu là tọa độ)
        origin_to_geocode = normalized_origin if ',' not in normalized_origin else origin
        dest_to_geocode = normalized_destination if ',' not in normalized_destination else destination
        origin_coords = self.geocode(origin_to_geocode, use_vietmap=use_vietmap)
        dest_coords = self.geocode(dest_to_geocode, use_vietmap=use_vietmap)
        
        if not origin_coords or not dest_coords:
            logger.warning(f"Cannot geocode locations for routing: {origin}, {destination}")
            return None
        
        # Validate geocoding: Kiểm tra khoảng cách đường thẳng TRƯỚC KHI tính routing
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(origin_coords['lat']), radians(origin_coords['lon'])
        lat2, lon2 = radians(dest_coords['lat']), radians(dest_coords['lon'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        straight_distance = 6371 * c
        
        logger.debug(f"Straight-line distance between geocoded points: {straight_distance:.1f} km")
        
        # Nếu khoảng cách đường thẳng > 300km, có thể geocoding sai (đặc biệt cho các địa điểm trong cùng khu vực)
        # Thử các biến thể tên cho các địa điểm nổi tiếng
        should_check_geocoding = False
        
        # Check 1: Khoảng cách > 300km và có thể là địa điểm trong cùng khu vực
        if straight_distance > 300:
            # Check 2: Nếu một trong hai địa điểm là địa điểm nổi tiếng có thể bị geocode sai
            origin_lower = origin.lower()
            dest_lower = destination.lower()
            famous_places = ['mỹ sơn', 'my son', 'sapa', 'sa pa', 'phú quốc', 'phu quoc', 'hội an', 'hoi an']
            if any(place in origin_lower for place in famous_places) or any(place in dest_lower for place in famous_places):
                should_check_geocoding = True
                logger.info(f"Detected potential geocoding error: straight-line distance {straight_distance:.1f}km for famous places")
        
        if should_check_geocoding:
            # Try geocoding variants for famous places
            # This is handled in the geocoding validation step above
            pass
        
        # Fallback to OpenRouteService
        # Geocode cả 2 điểm
        origin_coords = self.geocode(origin, use_vietmap=use_vietmap) # Use VietMap geocoding if available
        dest_coords = self.geocode(destination, use_vietmap=use_vietmap)
        
        if not origin_coords or not dest_coords:
            logger.warning(f"Cannot geocode locations for fallback routing: {origin}, {destination}")
            return None
        
        # Validate geocoding: Kiểm tra khoảng cách đường thẳng
        # Nếu quá xa (> 500km) và có thể là geocoding sai, thử các biến thể tên
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(origin_coords['lat']), radians(origin_coords['lon'])
        lat2, lon2 = radians(dest_coords['lat']), radians(dest_coords['lon'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        straight_distance = 6371 * c
        
        # Nếu khoảng cách đường thẳng > 300km, có thể geocoding sai (đặc biệt cho các địa điểm trong cùng khu vực)
        # Thử các biến thể tên cho các địa điểm nổi tiếng
        # Lưu ý: Một số route thực sự dài (như Hà Nội -> HCM ~1500km) nên chỉ check khi có dấu hiệu geocoding sai
        should_check_geocoding = False
        
        # Check 1: Khoảng cách > 300km và có thể là địa điểm trong cùng khu vực
        if straight_distance > 300:
            # Check 2: Nếu một trong hai địa điểm là địa điểm nổi tiếng có thể bị geocode sai
            origin_lower = origin.lower()
            dest_lower = destination.lower()
            famous_places = ['mỹ sơn', 'my son', 'sapa', 'sa pa', 'phú quốc', 'phu quoc', 'hội an', 'hoi an']
            if any(place in origin_lower for place in famous_places) or any(place in dest_lower for place in famous_places):
                should_check_geocoding = True
        
        if should_check_geocoding:
            logger.warning(f"Straight-line distance ({straight_distance:.1f}km) seems too large. Checking for geocoding errors...")
            
            # Mapping các địa điểm nổi tiếng với các biến thể tên
            origin_variants = []
            dest_variants = []
            
            origin_lower = origin.lower()
            dest_lower = destination.lower()
            
            # Thêm biến thể cho origin
            if 'mỹ sơn' in origin_lower or 'my son' in origin_lower:
                if 'quảng nam' not in origin_lower and 'thánh địa' not in origin_lower:
                    origin_variants = ['Thánh địa Mỹ Sơn', 'Mỹ Sơn, Quảng Nam']
            elif 'sapa' in origin_lower or 'sa pa' in origin_lower:
                if 'lào cai' not in origin_lower:
                    origin_variants = ['Sapa, Lào Cai']
            elif 'phú quốc' in origin_lower or 'phu quoc' in origin_lower:
                if 'kiên giang' not in origin_lower:
                    origin_variants = ['Phú Quốc, Kiên Giang']
            
            # Thêm biến thể cho destination
            if 'mỹ sơn' in dest_lower or 'my son' in dest_lower:
                if 'quảng nam' not in dest_lower and 'thánh địa' not in dest_lower:
                    dest_variants = ['Thánh địa Mỹ Sơn', 'Mỹ Sơn, Quảng Nam']
            elif 'sapa' in dest_lower or 'sa pa' in dest_lower:
                if 'lào cai' not in dest_lower:
                    dest_variants = ['Sapa, Lào Cai']
            elif 'phú quốc' in dest_lower or 'phu quoc' in dest_lower:
                if 'kiên giang' not in dest_lower:
                    dest_variants = ['Phú Quốc, Kiên Giang']
            
            # Thử các biến thể
            best_origin_coords = origin_coords
            best_dest_coords = dest_coords
            best_distance = straight_distance
            
            for orig_var in origin_variants:
                for dest_var in (dest_variants if dest_variants else [destination]):
                    logger.info(f"Trying geocoding variants: '{orig_var}' -> '{dest_var}'")
                    new_origin_coords = self.geocode(orig_var, use_vietmap=use_vietmap)
                    new_dest_coords = self.geocode(dest_var, use_vietmap=use_vietmap)
                    
                    if new_origin_coords and new_dest_coords:
                        # Tính lại khoảng cách đường thẳng
                        lat1_new, lon1_new = radians(new_origin_coords['lat']), radians(new_origin_coords['lon'])
                        lat2_new, lon2_new = radians(new_dest_coords['lat']), radians(new_dest_coords['lon'])
                        dlat_new = lat2_new - lat1_new
                        dlon_new = lon2_new - lon1_new
                        a_new = sin(dlat_new/2)**2 + cos(lat1_new) * cos(lat2_new) * sin(dlon_new/2)**2
                        c_new = 2 * atan2(sqrt(a_new), sqrt(1-a_new))
                        new_straight_distance = 6371 * c_new
                        
                        # Nếu khoảng cách mới hợp lý hơn (< 500km), dùng nó
                        if new_straight_distance < 500 and new_straight_distance < best_distance:
                            logger.info(f"Found better geocoding: {best_distance:.1f}km -> {new_straight_distance:.1f}km")
                            best_origin_coords = new_origin_coords
                            best_dest_coords = new_dest_coords
                            best_distance = new_straight_distance
                            # Update origin và destination để dùng trong routing
                            origin = orig_var
                            destination = dest_var
                
                if best_distance < 500:
                    break
            
            # Cập nhật tọa độ tốt nhất
            origin_coords = best_origin_coords
            dest_coords = best_dest_coords
            
        # Try OpenRouteService
        if self.openroute_api_key:
            try:
                url = f"{self.base_url}/v2/directions/{profile}"
                params = {
                    'api_key': self.openroute_api_key,
                    'start': f"{origin_coords['lon']},{origin_coords['lat']}",
                    'end': f"{dest_coords['lon']},{dest_coords['lat']}"
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if 'features' in data and len(data['features']) > 0:
                    props = data['features'][0]['properties']['segments'][0]
                    distance_km = props['distance'] / 1000
                    duration_min = props['duration'] / 60
                    
                    # Validate: Check if distance is reasonable (not > 2000km for domestic routes)
                    if distance_km > 2000:
                        logger.warning(f"OpenRouteService returned suspiciously large distance ({distance_km} km) for {origin} -> {destination}, trying Haversine fallback")
                        # Don't return, continue to Haversine fallback
                    else:
                        # Validate: Check if distance seems too short compared to straight-line distance
                        # This helps catch cases where routing data is incomplete (e.g., Mekong Delta)
                        haversine_dist = self._haversine_distance(
                            origin_coords['lat'], origin_coords['lon'],
                            dest_coords['lat'], dest_coords['lon']
                        )
                        
                        # If routing distance is less than 1.2x straight-line, likely incomplete data
                        # Apply correction factor for routes in Mekong Delta or rural areas
                        if distance_km < haversine_dist * 1.2 and haversine_dist > 50:
                            # Likely incomplete routing data, apply correction
                            correction_factor = 1.4  # Increase by 40% for incomplete data
                            corrected_distance = distance_km * correction_factor
                            corrected_duration = duration_min * correction_factor
                            
                            logger.warning(f"OpenRouteService distance ({distance_km:.1f}km) seems too short vs straight-line ({haversine_dist:.1f}km). Applying correction: {corrected_distance:.1f}km")
                            
                            distance_km = corrected_distance
                            duration_min = corrected_duration
                        
                        result = {
                            'distance_km': round(distance_km, 2),
                            'duration_minutes': round(duration_min, 1),
                            'route': data['features'][0]['geometry']['coordinates'],
                            'source': 'openrouteservice'
                        }
                        
                        # Cache result
                        if CACHE_AVAILABLE:
                            cache_key = generate_cache_key('route', normalized_origin, normalized_destination, profile, use_vietmap)
                            cache_set(cache_key, result, ttl=604800)  # 7 days
                            
                        return result
            except Exception as e:
                logger.warning(f"OpenRouteService routing failed: {e}")
        
        # Try OSRM (Open Source Routing Machine) - Free, no API key required
        # OSRM uses OSM data and provides real road distance
        try:
            logger.info(f"Trying OSRM routing for {origin} -> {destination}")
            osrm_url = "http://router.project-osrm.org/route/v1/driving"
            osrm_params = {
                'overview': 'false',  # Don't need full geometry
                'alternatives': 'false',
                'steps': 'false'
            }
            
            # OSRM uses lon,lat format (not lat,lon)
            osrm_coords = f"{origin_coords['lon']},{origin_coords['lat']};{dest_coords['lon']},{dest_coords['lat']}"
            osrm_response = requests.get(
                f"{osrm_url}/{osrm_coords}",
                params=osrm_params,
                timeout=10
            )
            
            if osrm_response.status_code == 200:
                osrm_data = osrm_response.json()
                if osrm_data.get('code') == 'Ok' and len(osrm_data.get('routes', [])) > 0:
                    route = osrm_data['routes'][0]
                    distance_km = route['distance'] / 1000  # Convert meters to km
                    duration_min = route['duration'] / 60  # Convert seconds to minutes
                    
                    # Validate: Check if distance is reasonable
                    if distance_km <= 2000:
                        logger.info(f"OSRM routing successful: {distance_km:.2f} km, {duration_min:.1f} min")
                        result = {
                            'distance_km': round(distance_km, 2),
                            'duration_minutes': round(duration_min, 1),
                            'source': 'osrm'
                        }
                        
                        # Cache result
                        if CACHE_AVAILABLE:
                            cache_key = generate_cache_key('route', normalized_origin, normalized_destination, profile, use_vietmap)
                            cache_set(cache_key, result, ttl=604800)  # 7 days
                        
                        return result
                    else:
                        logger.warning(f"OSRM returned suspiciously large distance ({distance_km} km), trying Haversine fallback")
        except Exception as e:
            logger.debug(f"OSRM routing failed: {e}, trying Haversine fallback")
        
        # Final Fallback: Haversine Distance (straight-line distance)
        # Apply road distance multiplier for more realistic estimates
        try:
            haversine_dist = self._haversine_distance(
                origin_coords['lat'], origin_coords['lon'],
                dest_coords['lat'], dest_coords['lon']
            )
            
            # Apply road distance multiplier (roads are typically 1.3-1.6x longer than straight line)
            # For Vietnam, use 1.5x multiplier for rural areas, 1.3x for urban
            # Check if route is likely rural (long distance or specific regions)
            is_rural_route = haversine_dist > 100  # Routes > 100km likely involve rural roads
            
            if is_rural_route:
                road_multiplier = 1.5  # Rural roads are more winding
            else:
                road_multiplier = 1.3  # Urban routes are more direct
            
            dist = haversine_dist * road_multiplier
            
            # Estimate duration with realistic speeds
            # Rural roads: 40-50 km/h average, urban: 30-40 km/h
            if is_rural_route:
                avg_speed = 45  # km/h for rural roads
            else:
                avg_speed = 35  # km/h for urban roads
            
            duration = (dist / avg_speed) * 60
            
            logger.info(f"Using Haversine fallback for {origin} -> {destination}: {haversine_dist:.2f} km (straight) -> {dist:.2f} km (road estimate)")
            
            return {
                'distance_km': round(dist, 2),
                'duration_minutes': round(duration, 1),
                'source': 'haversine_estimate'
            }
        except Exception as e:
            logger.error(f"Haversine calculation failed: {e}")
            return None

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate haversine distance between two points in km"""
        import math
        R = 6371  # Radius of Earth in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
            

    
    def find_nearby_places(
        self,
        location: str,
        radius_km: float = 10.0,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm địa điểm trong bán kính
        
        Args:
            location: Tên địa điểm trung tâm
            radius_km: Bán kính tìm kiếm (km)
            categories: Danh sách loại địa điểm (optional)
            
        Returns:
            List các địa điểm gần đó
        """
        coords = self.geocode(location)
        if not coords:
            return []

        results: List[Dict[str, Any]] = []

        # Nếu có VietMap, ưu tiên dùng Nearby Places từ VietMap
        if self.vietmap:
            try:
                search_query = None
                if categories:
                    # Ghép list categories thành query đơn giản
                    search_query = " ".join(str(c) for c in categories if c)

                vietmap_results = self.vietmap.nearby_places(
                    lat=coords['lat'],
                    lon=coords['lon'],
                    query=search_query,
                    radius=radius_km,
                    limit=20,
                )

                if isinstance(vietmap_results, list):
                    results = vietmap_results
            except Exception as e:
                logger.warning(f"VietMap nearby places error for {location}: {e}")
                results = []
            
        # TODO: Tích hợp với OpenTripMap hoặc Places API
        # Hiện tại return empty list
        return results


# Singleton instance
_geo_tools = None

def get_geo_tools() -> GeoTools:
    """Get singleton GeoTools instance"""
    global _geo_tools
    if _geo_tools is None:
        _geo_tools = GeoTools()
    return _geo_tools

