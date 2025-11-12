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
            location: Tên địa điểm (ví dụ: "Hà Nội", "TP. Hồ Chí Minh")
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
            try:
                result = self.vietmap.geocode(location)
                if result:
                    logger.debug(f"Geocoded via VietMap: {location}")
                    # Cache result
                    if CACHE_AVAILABLE:
                        cache_key = generate_cache_key('geocode', location, country, use_vietmap)
                        cache_set(cache_key, result, ttl=604800)  # 7 days
                    return result
            except Exception as e:
                logger.debug(f"VietMap geocoding failed, trying OpenRouteService: {e}")
        
        # Fallback to OpenRouteService
        if not self.openroute_api_key:
            logger.warning("No geocoding API key available (OPENROUTE_API_KEY or VIETMAP_API_KEY)")
            return None
            
        try:
            url = f"{self.base_url}/geocode/search"
            params = {
                'api_key': self.openroute_api_key,
                'text': location,
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
                
                # Cache result for 7 days (geocoding rarely changes)
                if CACHE_AVAILABLE:
                    cache_key = generate_cache_key('geocode', location, country, use_vietmap)
                    cache_set(cache_key, result, ttl=604800)
                
                return result
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
            
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
        # Check cache first
        if CACHE_AVAILABLE:
            cache_key = generate_cache_key('route', origin, destination, profile, use_vietmap)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for route: {origin} -> {destination}")
                return cached_result
        
        # Map profile names
        profile_map = {
            'driving-car': 'car',
            'cycling-regular': 'bike',
            'foot-walking': 'foot'
        }
        vietmap_profile = profile_map.get(profile, 'car')
        
        # Thử VietMap trước nếu có
        if use_vietmap and self.vietmap:
            try:
                result = self.vietmap.calculate_distance_time(origin, destination, vietmap_profile)
                if result:
                    logger.debug(f"Routing via VietMap: {origin} -> {destination}")
                    # Cache result
                    if CACHE_AVAILABLE:
                        cache_key = generate_cache_key('route', origin, destination, profile, use_vietmap)
                        cache_set(cache_key, result, ttl=86400)  # 24 hours
                    return result
            except Exception as e:
                logger.debug(f"VietMap routing failed, trying OpenRouteService: {e}")
        
        # Fallback to OpenRouteService
        # Geocode cả 2 điểm
        origin_coords = self.geocode(origin, use_vietmap=False)
        dest_coords = self.geocode(destination, use_vietmap=False)
        
        if not origin_coords or not dest_coords:
            return None
            
        try:
            url = f"{self.base_url}/v2/directions/{profile}"
            params = {
                'api_key': self.openroute_api_key,
                'start': f"{origin_coords['lon']},{origin_coords['lat']}",
                'end': f"{dest_coords['lon']},{dest_coords['lat']}"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                properties = feature.get('properties', {})
                summary = properties.get('summary', {})
                
                distance_m = summary.get('distance', 0)
                duration_s = summary.get('duration', 0)
                
                result = {
                    'distance_km': round(distance_m / 1000, 2),
                    'duration_minutes': round(duration_s / 60, 1),
                    'distance_meters': int(distance_m),
                    'duration_seconds': int(duration_s),
                    'route': feature.get('geometry', {})
                }
                
                # Cache result for 24 hours
                if CACHE_AVAILABLE:
                    cache_key = generate_cache_key('route', origin, destination, profile, use_vietmap)
                    cache_set(cache_key, result, ttl=86400)
                
                return result
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            
        return None
    
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
            
        # TODO: Tích hợp với OpenTripMap hoặc Places API
        # Hiện tại return empty list
        return []


# Singleton instance
_geo_tools = None

def get_geo_tools() -> GeoTools:
    """Get singleton GeoTools instance"""
    global _geo_tools
    if _geo_tools is None:
        _geo_tools = GeoTools()
    return _geo_tools

