"""
VietMap Tools - Công cụ địa lý từ VietMap API
==============================================
VietMap là dịch vụ bản đồ chuyên biệt cho Việt Nam với:
- Geocoding chính xác cho địa chỉ Việt Nam
- Routing với dữ liệu đường phố Việt Nam cập nhật
- Autocomplete cho tìm kiếm địa chỉ
- TSP/VRP cho tối ưu hóa lộ trình

API Documentation: https://maps.vietmap.vn/docs/map-api/overview/
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


class VietMapTools:
    """Công cụ địa lý từ VietMap API"""
    
    def __init__(self):
        # Try to get from Django settings first (if running in Django context)
        try:
            from django.conf import settings
            self.vietmap_api_key = getattr(settings, 'VIETMAP_API_KEY', '')
        except (ImportError, AttributeError):
            # Fallback to environment variable
            self.vietmap_api_key = os.getenv('VIETMAP_API_KEY', '')
        
        # VietMap API base URL
        self.base_url = "https://maps.vietmap.vn/api"
        
    @lru_cache(maxsize=1000)
    def geocode(self, location: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Geocoding - Chuyển đổi địa chỉ/tên địa điểm thành tọa độ
        
        Args:
            location: Địa chỉ hoặc tên địa điểm (ví dụ: "Hà Nội", "123 Nguyễn Huệ, Quận 1, TP.HCM")
            limit: Số kết quả tối đa (mặc định: 1)
            
        Returns:
            Dict với 'lat', 'lon', 'formatted_address' hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            url = f"{self.base_url}/geocoding"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'text': location,
                'limit': limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # VietMap API response format (cần điều chỉnh theo format thực tế)
            if isinstance(data, list) and len(data) > 0:
                result = data[0]
                return {
                    'lat': result.get('lat') or result.get('latitude'),
                    'lon': result.get('lon') or result.get('longitude') or result.get('lng'),
                    'formatted_address': result.get('display_name') or result.get('address') or location,
                    'confidence': result.get('confidence', 0.0)
                }
            elif isinstance(data, dict) and data.get('data'):
                result = data['data'][0] if isinstance(data['data'], list) else data['data']
                return {
                    'lat': result.get('lat') or result.get('latitude'),
                    'lon': result.get('lon') or result.get('longitude') or result.get('lng'),
                    'formatted_address': result.get('display_name') or result.get('address') or location,
                    'confidence': result.get('confidence', 0.0)
                }
        except Exception as e:
            logger.error(f"VietMap geocoding error for {location}: {e}")
            
        return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Reverse Geocoding - Chuyển đổi tọa độ thành địa chỉ
        
        Args:
            lat: Vĩ độ
            lon: Kinh độ
            
        Returns:
            Dict với 'formatted_address' hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            url = f"{self.base_url}/reverse"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'lat': lat,
                'lon': lon
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            if isinstance(data, dict):
                result = data.get('data') or data
                return {
                    'formatted_address': result.get('display_name') or result.get('address'),
                    'lat': lat,
                    'lon': lon
                }
        except Exception as e:
            logger.error(f"VietMap reverse geocoding error for ({lat}, {lon}): {e}")
            
        return None
    
    def calculate_distance_time(
        self,
        origin: str,
        destination: str,
        profile: str = "car"  # car, bike, foot
    ) -> Optional[Dict[str, Any]]:
        """
        Tính khoảng cách và thời gian di chuyển giữa 2 điểm
        
        Args:
            origin: Điểm xuất phát (địa chỉ hoặc "lat,lon")
            destination: Điểm đến (địa chỉ hoặc "lat,lon")
            profile: Loại phương tiện (car, bike, foot)
            
        Returns:
            Dict với 'distance_km', 'duration_minutes', 'route' hoặc None
        """
        # Geocode cả 2 điểm nếu cần
        if ',' not in origin or ',' not in destination:
            origin_coords = self.geocode(origin)
            dest_coords = self.geocode(destination)
            
            if not origin_coords or not dest_coords:
                return None
            
            origin = f"{origin_coords['lat']},{origin_coords['lon']}"
            destination = f"{dest_coords['lat']},{dest_coords['lon']}"
        
        try:
            url = f"{self.base_url}/route"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'point': f"{origin};{destination}",
                'profile': profile
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse routing response
            if isinstance(data, dict) and data.get('routes'):
                route = data['routes'][0]
                summary = route.get('summary', {}) or route.get('distance', {})
                
                distance_m = summary.get('distance', 0) if isinstance(summary, dict) else summary
                duration_s = summary.get('duration', 0) if isinstance(summary, dict) else route.get('duration', 0)
                
                # If distance_m is 0, try alternative paths
                if distance_m == 0 and route.get('distance'):
                    distance_m = route['distance']
                if duration_s == 0 and route.get('duration'):
                    duration_s = route['duration']
                
                return {
                    'distance_km': round(distance_m / 1000, 2) if distance_m else 0,
                    'duration_minutes': round(duration_s / 60, 1) if duration_s else 0,
                    'distance_meters': int(distance_m) if distance_m else 0,
                    'duration_seconds': int(duration_s) if duration_s else 0,
                    'route': route.get('geometry', {})
                }
        except Exception as e:
            logger.error(f"VietMap routing error: {e}")
            
        return None
    
    def autocomplete(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Autocomplete - Tìm kiếm gợi ý địa chỉ khi người dùng gõ
        
        Args:
            query: Từ khóa tìm kiếm
            limit: Số kết quả tối đa
            
        Returns:
            List các địa chỉ gợi ý
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        try:
            url = f"{self.base_url}/autocomplete"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'text': query,
                'limit': limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse autocomplete response
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict) and data.get('data'):
                results = data['data'] if isinstance(data['data'], list) else [data['data']]
            
            formatted_results = []
            for item in results[:limit]:
                formatted_results.append({
                    'display_name': item.get('display_name') or item.get('address') or item.get('name'),
                    'lat': item.get('lat') or item.get('latitude'),
                    'lon': item.get('lon') or item.get('longitude') or item.get('lng'),
                    'address': item.get('address') or item.get('display_name')
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"VietMap autocomplete error for {query}: {e}")
            
        return []
    
    def optimize_route(
        self,
        points: List[str],  # List of addresses or "lat,lon"
        optimize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Tối ưu hóa lộ trình (TSP/VRP) - Tìm lộ trình ngắn nhất qua nhiều điểm
        
        Args:
            points: Danh sách các điểm cần đi qua
            optimize: Có tối ưu hóa thứ tự không
            
        Returns:
            Dict với lộ trình tối ưu hoặc None
        """
        if not self.vietmap_api_key or len(points) < 2:
            return None
        
        try:
            # Geocode points if needed
            coords = []
            for point in points:
                if ',' in point:
                    coords.append(point)
                else:
                    geocoded = self.geocode(point)
                    if geocoded:
                        coords.append(f"{geocoded['lat']},{geocoded['lon']}")
            
            if len(coords) < 2:
                return None
            
            url = f"{self.base_url}/optimize"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'point': ';'.join(coords),
                'optimize': 'true' if optimize else 'false'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logger.error(f"VietMap route optimization error: {e}")
            
        return None


# Singleton instance
_vietmap_tools = None

def get_vietmap_tools() -> VietMapTools:
    """Get singleton VietMapTools instance"""
    global _vietmap_tools
    if _vietmap_tools is None:
        _vietmap_tools = VietMapTools()
    return _vietmap_tools

