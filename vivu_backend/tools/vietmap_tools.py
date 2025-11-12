"""
VietMap Tools - Công cụ địa lý từ VietMap API
==============================================
VietMap là dịch vụ bản đồ chuyên biệt cho Việt Nam với:
- Geocoding chính xác cho địa chỉ Việt Nam
- Reverse Geocoding (tọa độ → địa chỉ)
- Routing với dữ liệu đường phố Việt Nam cập nhật
- Autocomplete cho tìm kiếm địa chỉ
- TSP/VRP cho tối ưu hóa lộ trình
- Isochrone cho phân tích vùng tiếp cận
- Search places (tìm kiếm địa điểm)

API Documentation:
- Overview: https://maps.vietmap.vn/docs/map-api/overview/
- Geocoding: https://maps.vietmap.vn/docs/map-api/geocoding/
- Routing: https://maps.vietmap.vn/docs/map-api/routing/
- Search: https://maps.vietmap.vn/docs/map-api/search/

Đăng ký API key: https://maps.vietmap.vn/
Hỗ trợ: 089.616.4567 hoặc maps.info@vietmap.vn
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
        
        # Thử các endpoint khác nhau
        endpoints_to_try = [
            ('/geocoding', {'apikey': self.vietmap_api_key, 'text': location}),
            ('/search', {'apikey': self.vietmap_api_key, 'text': location, 'limit': limit}),
            ('/migrate-address/v3', {'apikey': self.vietmap_api_key, 'text': location}),
        ]
        
        for endpoint, params in endpoints_to_try:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, params=params, timeout=10)
                
                # Nếu 401 Unauthorized, có thể là API key sai hoặc endpoint không đúng
                if response.status_code == 401:
                    logger.warning(f"VietMap API 401 Unauthorized for {endpoint} - check API key")
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Parse response - thử nhiều format
                result = None
                
                # Format 1: List of results
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    lat = result.get('lat') or result.get('latitude') or result.get('y')
                    lon = result.get('lon') or result.get('longitude') or result.get('lng') or result.get('x')
                    
                    if lat is not None and lon is not None:
                        return {
                            'lat': float(lat),
                            'lon': float(lon),
                            'formatted_address': result.get('display_name') or result.get('address') or result.get('name') or location,
                            'confidence': result.get('confidence', 0.8)
                        }
                
                # Format 2: Dict with 'data' key
                elif isinstance(data, dict):
                    results = data.get('data', [])
                    if isinstance(results, list) and len(results) > 0:
                        result = results[0]
                    elif isinstance(data.get('data'), dict):
                        result = data.get('data')
                    else:
                        # Thử lấy từ boundaries nếu có
                        boundaries = data.get('boundaries', [])
                        if boundaries and isinstance(boundaries, list) and len(boundaries) > 0:
                            boundary = boundaries[0]
                            # Boundaries có thể chứa geometry với coordinates
                            if isinstance(boundary, dict):
                                geometry = boundary.get('geometry', {})
                                if geometry:
                                    coords = geometry.get('coordinates', [])
                                    if coords and len(coords) >= 2:
                                        return {
                                            'lat': float(coords[1]),
                                            'lon': float(coords[0]),
                                            'formatted_address': data.get('display', data.get('address', location)),
                                            'confidence': 0.8
                                        }
                    
                    if result:
                        lat = result.get('lat') or result.get('latitude') or result.get('y')
                        lon = result.get('lon') or result.get('longitude') or result.get('lng') or result.get('x')
                        
                        if lat is not None and lon is not None:
                            return {
                                'lat': float(lat),
                                'lon': float(lon),
                                'formatted_address': result.get('display_name') or result.get('address') or result.get('name') or data.get('display', location),
                                'confidence': result.get('confidence', 0.7)
                            }
                
                # Nếu không parse được coordinates, log và tiếp tục thử endpoint khác
                logger.debug(f"VietMap {endpoint} returned data but no coordinates found: {type(data)}")
                
            except requests.exceptions.RequestException as e:
                logger.debug(f"VietMap {endpoint} failed: {e}")
                continue
            except Exception as e:
                logger.debug(f"VietMap {endpoint} error: {e}")
                continue
        
        # Nếu tất cả endpoints đều fail, return None để fallback về OpenRouteService
        logger.warning(f"VietMap geocoding failed for all endpoints: {location}")
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
            
            if not origin_coords or not origin_coords.get('lat') or not origin_coords.get('lon'):
                logger.warning(f"Cannot geocode origin: {origin}")
                return None
            
            if not dest_coords or not dest_coords.get('lat') or not dest_coords.get('lon'):
                logger.warning(f"Cannot geocode destination: {destination}")
                return None
            
            origin = f"{origin_coords['lat']},{origin_coords['lon']}"
            destination = f"{dest_coords['lat']},{dest_coords['lon']}"
        
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            # Sử dụng endpoint v3 mới với API key trong query parameter
            url = f"{self.base_url}/route/v3"
            
            # Parse origin and destination coordinates
            origin_parts = origin.split(',')
            dest_parts = destination.split(',')
            
            if len(origin_parts) != 2 or len(dest_parts) != 2:
                logger.error(f"Invalid coordinate format: origin={origin}, destination={destination}")
                return None
            
            origin_lat = origin_parts[0].strip()
            origin_lon = origin_parts[1].strip()
            dest_lat = dest_parts[0].strip()
            dest_lon = dest_parts[1].strip()
            
            # Map profile to vehicle (car, bike, foot, motorcycle)
            vehicle_map = {
                'car': 'car',
                'bike': 'bike',
                'bicycle': 'bike',
                'foot': 'foot',
                'walk': 'foot',
                'motorcycle': 'motorcycle',
                'motor': 'motorcycle'
            }
            vehicle = vehicle_map.get(profile.lower(), 'car')
            
            # Build params với API key trong query parameter và point riêng biệt
            # requests library không hỗ trợ duplicate keys trong dict, nên dùng list of tuples
            from urllib.parse import urlencode
            
            # Build params list để hỗ trợ multiple 'point' parameters
            params_list = [
                ('apikey', self.vietmap_api_key),
                ('point', f"{origin_lat},{origin_lon}"),  # Point đầu tiên
                ('point', f"{dest_lat},{dest_lon}"),      # Point thứ hai
                ('points_encoded', 'false'),  # Không encode để lấy geometry dễ parse
                ('vehicle', vehicle)
            ]
            
            # Encode URL với list of tuples để giữ multiple 'point' parameters
            query_string = urlencode(params_list)
            url_with_params = f"{url}?{query_string}"
            
            response = requests.get(url_with_params, timeout=10)
            
            # Nếu 401, log và return None để fallback
            if response.status_code == 401:
                logger.error(f"VietMap API 401 Unauthorized - Check API key: {self.vietmap_api_key[:10]}...")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Parse routing response từ v3 API
            # Format có thể khác, cần xử lý nhiều format
            route = None
            distance_m = 0
            duration_s = 0
            
            # Format 1: Có 'routes' key
            if isinstance(data, dict) and data.get('routes'):
                route = data['routes'][0]
                summary = route.get('summary', {})
                
                if isinstance(summary, dict):
                    distance_m = summary.get('distance', 0)
                    duration_s = summary.get('duration', 0)
                else:
                    distance_m = route.get('distance', 0)
                    duration_s = route.get('duration', 0)
            
            # Format 2: Response trực tiếp có distance/duration
            elif isinstance(data, dict):
                if 'distance' in data:
                    distance_m = data.get('distance', 0)
                if 'duration' in data:
                    duration_s = data.get('duration', 0)
                route = data
            
            # Format 3: Có 'paths' key (một số API routing dùng format này)
            elif isinstance(data, dict) and data.get('paths'):
                path = data['paths'][0]
                distance_m = path.get('distance', 0)
                duration_s = path.get('time', 0) / 1000  # Convert ms to seconds if needed
                route = path
            
            # Convert units nếu cần
            if duration_s > 0 and duration_s < 100:  # Có thể là phút, convert sang giây
                duration_s = duration_s * 60
            
            return {
                'distance_km': round(distance_m / 1000, 2) if distance_m else 0,
                'duration_minutes': round(duration_s / 60, 1) if duration_s else 0,
                'distance_meters': int(distance_m) if distance_m else 0,
                'duration_seconds': int(duration_s) if duration_s else 0,
                'route': route.get('geometry', {}) if route else {}
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"VietMap routing HTTP error: {e} - Status: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}")
            if hasattr(e, 'response') and e.response.status_code == 401:
                logger.error("VietMap API key may be invalid or expired")
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
    
    def search_places(
        self,
        query: str,
        location: Optional[str] = None,  # "lat,lon" hoặc địa chỉ
        radius: Optional[float] = None,  # Bán kính tìm kiếm (km)
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm địa điểm (places) - Nhà hàng, khách sạn, địa điểm du lịch, etc.
        
        Args:
            query: Từ khóa tìm kiếm (ví dụ: "nhà hàng", "khách sạn", "bảo tàng")
            location: Vị trí trung tâm (tọa độ "lat,lon" hoặc địa chỉ)
            radius: Bán kính tìm kiếm (km) - chỉ áp dụng khi có location
            limit: Số kết quả tối đa
            
        Returns:
            List các địa điểm tìm được
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        try:
            # Sử dụng search endpoint với các tham số
            url = f"{self.base_url}/search"
            params = {
                'apikey': self.vietmap_api_key,
                'text': query,
                'limit': limit
            }
            
            # Nếu có location, thêm vào params
            if location:
                # Nếu location là địa chỉ, geocode trước
                if ',' not in location:
                    geocoded = self.geocode(location)
                    if geocoded:
                        location = f"{geocoded['lat']},{geocoded['lon']}"
                
                if ',' in location:
                    try:
                        parts = location.split(',')
                        if len(parts) >= 2:
                            lat_str = parts[0].strip()
                            lon_str = parts[1].strip()
                            # Validate và parse coordinates
                            lat = float(lat_str)
                            lon = float(lon_str)
                            # Validate range (Vietnam: lat ~8-23, lon ~102-110)
                            if 8 <= lat <= 23 and 102 <= lon <= 110:
                                params['lat'] = lat
                                params['lon'] = lon
                            else:
                                logger.warning(f"Coordinates out of Vietnam range: lat={lat}, lon={lon}")
                        else:
                            logger.warning(f"Invalid location format (not enough parts): {location}")
                    except (ValueError, IndexError) as e:
                        logger.error(f"VietMap parse location error: {e}, location={location}")
                        # Fallback: try geocoding again
                        geocoded = self.geocode(location)
                        if geocoded:
                            params['lat'] = geocoded['lat']
                            params['lon'] = geocoded['lon']
                    
                    if radius:
                        params['radius'] = radius * 1000  # Convert km to meters
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse search results
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = data.get('data', [])
                if not isinstance(results, list):
                    results = [results] if results else []
            
            formatted_results = []
            for item in results[:limit]:
                # Safe coordinate parsing
                lat = None
                lon = None
                try:
                    lat_val = item.get('lat') or item.get('latitude') or item.get('y')
                    lon_val = item.get('lon') or item.get('longitude') or item.get('lng') or item.get('x')
                    if lat_val is not None:
                        lat = float(lat_val)
                    if lon_val is not None:
                        lon = float(lon_val)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not parse coordinates from item: {item.get('name', 'unknown')}, error: {e}")
                
                formatted_results.append({
                    'name': item.get('name') or item.get('display_name') or item.get('address'),
                    'address': item.get('address') or item.get('display_name'),
                    'lat': lat,
                    'lon': lon,
                    'category': item.get('category') or item.get('type'),
                    'rating': item.get('rating'),
                    'phone': item.get('phone'),
                    'website': item.get('website'),
                    'distance': item.get('distance'),  # Khoảng cách nếu có location
                    'source': 'vietmap'
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"VietMap search places error for '{query}': {e}")
        
        return []
    
    def nearby_places(
        self,
        lat: float,
        lon: float,
        query: Optional[str] = None,  # Loại địa điểm (ví dụ: "nhà hàng", "khách sạn")
        radius: float = 5.0,  # Bán kính (km)
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tìm địa điểm gần đây (Nearby Places)
        
        Args:
            lat: Vĩ độ
            lon: Kinh độ
            query: Loại địa điểm (optional, ví dụ: "nhà hàng", "khách sạn", "bảo tàng")
            radius: Bán kính tìm kiếm (km, mặc định: 5km)
            limit: Số kết quả tối đa
            
        Returns:
            List các địa điểm gần đây
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        # Sử dụng search với location và radius
        search_query = query or "địa điểm"
        return self.search_places(
            query=search_query,
            location=f"{lat},{lon}",
            radius=radius,
            limit=limit
        )
    
    def isochrone(
        self,
        lat: float,
        lon: float,
        profile: str = "car",  # car, bike, foot
        time_limit: int = 30,  # Thời gian tối đa (phút)
        distance_limit: Optional[float] = None  # Khoảng cách tối đa (km)
    ) -> Optional[Dict[str, Any]]:
        """
        Phân tích vùng tiếp cận (Isochrone) - Tìm vùng có thể đến được trong thời gian/khoảng cách nhất định
        
        Args:
            lat: Vĩ độ điểm xuất phát
            lon: Kinh độ điểm xuất phát
            profile: Loại phương tiện (car, bike, foot)
            time_limit: Thời gian tối đa (phút)
            distance_limit: Khoảng cách tối đa (km, optional)
            
        Returns:
            Dict với thông tin vùng tiếp cận hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            url = f"{self.base_url}/isochrone"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'point': f"{lat},{lon}",
                'profile': profile,
                'time_limit': time_limit * 60  # Convert minutes to seconds
            }
            
            if distance_limit:
                params['distance_limit'] = distance_limit * 1000  # Convert km to meters
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logger.error(f"VietMap isochrone error for ({lat}, {lon}): {e}")
        
        return None


# Singleton instance
_vietmap_tools = None

def get_vietmap_tools() -> VietMapTools:
    """Get singleton VietMapTools instance"""
    global _vietmap_tools
    if _vietmap_tools is None:
        _vietmap_tools = VietMapTools()
    return _vietmap_tools

